from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from accounts.models import HospitalProfile
from inventory.models import BloodStock
import random
class Command(BaseCommand):
    help = 'Seed initial data (superuser, hospital user, groups, sample stocks)'
    def handle(self, *args, **options):
        if not Group.objects.filter(name='Hospital').exists():
            Group.objects.create(name='Hospital')
            self.stdout.write('Created group Hospital')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin','admin@example.com','adminpass')
            self.stdout.write('Created superuser admin/adminpass')
        if not User.objects.filter(username='hospital1').exists():
            u = User.objects.create_user('hospital1','hosp1@example.com','hospass')
            grp = Group.objects.get(name='Hospital')
            u.groups.add(grp)
            hp = HospitalProfile.objects.create(user=u, name='City Hospital', address='123 Main St')
            self.stdout.write('Created hospital user hospital1/hospass and profile')
            # sample stocks
            groups = ['A+','A-','B+','B-','AB+','AB-','O+','O-']
            for i,g in enumerate(groups, start=1):
                sid = f'H{1000+i}'
                BloodStock.objects.create(blood_sample_id=sid,blood_group=g,units=random.randint(5,20),hospital=hp)
            self.stdout.write('Created sample stocks')
        else:
            self.stdout.write('Users already exist')
