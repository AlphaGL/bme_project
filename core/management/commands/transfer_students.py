# core/management/commands/transfer_students.py
import psycopg2
from django.core.management.base import BaseCommand
from core.models import RegisteredRegNumber


class Command(BaseCommand):
    help = 'Transfer students from old database to RegisteredRegNumber model'

    def handle(self, *args, **kwargs):
        # OLD DATABASE CONNECTION (Neon)
        old_db_url = "postgresql://neondb_owner:npg_FwbGQ8WoVn1r@ep-odd-glitter-ad4ndj5m-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
        
        try:
            self.stdout.write(self.style.WARNING('Connecting to old database...'))
            old_conn = psycopg2.connect(old_db_url)
            old_cursor = old_conn.cursor()
            
            # First, list all tables in the database
            self.stdout.write(self.style.WARNING('\nDiscovering tables in old database...'))
            old_cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname='public'
                ORDER BY tablename
            """)
            all_tables = old_cursor.fetchall()
            
            self.stdout.write(self.style.SUCCESS(f'\nFound {len(all_tables)} tables:'))
            for table in all_tables:
                self.stdout.write(f'  - {table[0]}')
            
            # Try common Student table names
            possible_names = [
                'core_student',
                'student',
                'students',
                'auth_student',
                'voting_student',
                'accounts_student',
                'users_student',
            ]
            
            student_table = None
            for table_name in possible_names:
                old_cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table_name,))
                
                if old_cursor.fetchone()[0]:
                    # Check if it has the required columns
                    old_cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = %s
                    """, (table_name,))
                    columns = [col[0] for col in old_cursor.fetchall()]
                    
                    if 'reg_number' in columns and 'full_name' in columns:
                        student_table = table_name
                        self.stdout.write(self.style.SUCCESS(f'\n✓ Found student table: {student_table}'))
                        self.stdout.write(f'  Columns: {", ".join(columns)}')
                        break
            
            if not student_table:
                self.stdout.write(self.style.ERROR('\n✗ Could not find a student table with reg_number and full_name columns'))
                self.stdout.write(self.style.WARNING('\nPlease tell me which table name to use from the list above.'))
                return
            
            # Fetch students from old database
            self.stdout.write(self.style.WARNING(f'\nFetching students from {student_table}...'))
            old_cursor.execute(f"""
                SELECT reg_number, full_name 
                FROM {student_table}
                WHERE is_active = true
            """)
            
            students = old_cursor.fetchall()
            self.stdout.write(self.style.SUCCESS(f'Found {len(students)} active students'))
            
            # Transfer to new database
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for reg_number, full_name in students:
                try:
                    obj, created = RegisteredRegNumber.objects.update_or_create(
                        reg_number=reg_number,
                        defaults={
                            'full_name': full_name if full_name else None,
                            'level': '100',  # Default level - you can adjust this
                            'is_active': True
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'✓ Created: {reg_number} - {full_name}')
                    else:
                        updated_count += 1
                        self.stdout.write(f'↻ Updated: {reg_number} - {full_name}')
                        
                except Exception as e:
                    skipped_count += 1
                    self.stdout.write(self.style.ERROR(f'✗ Error with {reg_number}: {str(e)}'))
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\n' + '='*50))
            self.stdout.write(self.style.SUCCESS('TRANSFER COMPLETE!'))
            self.stdout.write(self.style.SUCCESS('='*50))
            self.stdout.write(f'Created: {created_count} new registrations')
            self.stdout.write(f'Updated: {updated_count} existing registrations')
            self.stdout.write(f'Skipped: {skipped_count} (errors)')
            self.stdout.write(f'Total processed: {len(students)}')
            self.stdout.write(self.style.SUCCESS('='*50))
            
            # Close connections
            old_cursor.close()
            old_conn.close()
            
        except psycopg2.Error as e:
            self.stdout.write(self.style.ERROR(f'\nDatabase error: {str(e)}'))
            self.stdout.write(self.style.ERROR('Please check your database credentials and connection.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nUnexpected error: {str(e)}'))