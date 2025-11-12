from django.core.management.base import BaseCommand
from core.models import RegisteredRegNumber

class Command(BaseCommand):
    help = 'Add a single registration number'

    def add_arguments(self, parser):
        parser.add_argument('reg_number', type=str, help='Registration number')
        parser.add_argument('--name', type=str, help='Student full name')
        parser.add_argument('--level', type=str, default='100', help='Student level')

    def handle(self, *args, **options):
        reg_number = options['reg_number']
        full_name = options.get('name')
        level = options['level']
        
        try:
            obj, created = RegisteredRegNumber.objects.update_or_create(
                reg_number=reg_number,
                defaults={
                    'full_name': full_name,
                    'level': level,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successfully added: {reg_number}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successfully updated: {reg_number}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error: {str(e)}')
            )
