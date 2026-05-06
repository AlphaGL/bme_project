from django.core.management.base import BaseCommand
from core.models import RegisteredRegNumber
import csv

class Command(BaseCommand):
    help = 'Import registration numbers from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--level',
            type=str,
            default='100',
            help='Default level if not specified in CSV'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        default_level = options['level']
        
        success_count = 0
        error_count = 0
        
        try:
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                
                # Expected CSV format: reg_number,full_name,level
                # Example: 202X1234567,John Doe,100
                
                for row in reader:
                    try:
                        reg_number = row.get('reg_number', '').strip()
                        full_name = row.get('full_name', '').strip()
                        level = row.get('level', default_level).strip()
                        
                        if not reg_number:
                            self.stdout.write(
                                self.style.WARNING(f'Skipping row with empty reg_number')
                            )
                            continue
                        
                        # Create or update
                        obj, created = RegisteredRegNumber.objects.update_or_create(
                            reg_number=reg_number,
                            defaults={
                                'full_name': full_name if full_name else None,
                                'level': level,
                                'is_active': True
                            }
                        )
                        
                        if created:
                            success_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'✓ Added: {reg_number}')
                            )
                        else:
                            success_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'✓ Updated: {reg_number}')
                            )
                            
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'✗ Error with {row}: {str(e)}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n=== Import Complete ===\n'
                        f'Success: {success_count}\n'
                        f'Errors: {error_count}'
                    )
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File not found: {csv_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )