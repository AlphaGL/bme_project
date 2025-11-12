from django.core.management.base import BaseCommand
from core.models import RegisteredRegNumber

class Command(BaseCommand):
    help = 'Add multiple registration numbers interactively'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                '\n=== Bulk Add Registration Numbers ===\n'
                'Enter registration numbers (one per line)\n'
                'Format: REG_NUMBER,NAME,LEVEL (name and level are optional)\n'
                'Type "done" when finished\n'
            )
        )
        
        count = 0
        
        while True:
            try:
                line = input('> ').strip()
                
                if line.lower() == 'done':
                    break
                
                if not line:
                    continue
                
                parts = [p.strip() for p in line.split(',')]
                reg_number = parts[0]
                full_name = parts[1] if len(parts) > 1 else None
                level = parts[2] if len(parts) > 2 else '100'
                
                obj, created = RegisteredRegNumber.objects.update_or_create(
                    reg_number=reg_number,
                    defaults={
                        'full_name': full_name,
                        'level': level,
                        'is_active': True
                    }
                )
                
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Added: {reg_number}')
                )
                
            except KeyboardInterrupt:
                self.stdout.write('\n')
                break
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total added: {count}')
        )