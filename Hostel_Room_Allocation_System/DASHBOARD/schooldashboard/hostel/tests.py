from django.test import TestCase, Client
from django.urls import reverse
from .models import Hostel
from .forms import HostelForm


class HostelModelTest(TestCase):
    def setUp(self):
        self.hostel = Hostel.objects.create(
            student_name="Rahul Sharma",
            room_no="101",
            block="Block A",
            floor=1,
            warden_name="Dr. V. K. Patil",
            rent=4500.00,
            status="Occupied"
        )

    def test_hostel_creation(self):
        self.assertEqual(self.hostel.student_name, "Rahul Sharma")
        self.assertEqual(self.hostel.room_no, "101")
        self.assertEqual(self.hostel.block, "Block A")
        self.assertEqual(self.hostel.status, "Occupied")

    def test_hostel_str_representation(self):
        self.assertEqual(str(self.hostel), "Rahul Sharma - Room 101")


class HostelFormTest(TestCase):
    def test_valid_hostel_form(self):
        data = {
            'student_name': 'Amit Kumar',
            'room_no': '202',
            'block': 'Block B',
            'floor': 2,
            'warden_name': 'Prof. Deshmukh',
            'rent': 5000.00,
            'status': 'Occupied',
        }
        form = HostelForm(data=data)
        self.assertTrue(form.is_valid())

    def test_negative_rent_validation(self):
        data = {
            'student_name': 'Amit Kumar',
            'room_no': '202',
            'block': 'Block B',
            'floor': 2,
            'warden_name': 'Prof. Deshmukh',
            'rent': -100.00,
            'status': 'Occupied',
        }
        form = HostelForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rent', form.errors)


class HostelViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.h1 = Hostel.objects.create(
            student_name="Priya Patel",
            room_no="101",
            block="Block A",
            floor=1,
            warden_name="Dr. Patil",
            rent=4500.00,
            status="Occupied"
        )
        self.h2 = Hostel.objects.create(
            student_name="Vacant / Unallocated",
            room_no="102",
            block="Block A",
            floor=1,
            warden_name="Dr. Patil",
            rent=4500.00,
            status="Vacant"
        )
        self.h3 = Hostel.objects.create(
            student_name="Suresh Jadhav",
            room_no="201",
            block="Block B",
            floor=2,
            warden_name="Prof. Rao",
            rent=5500.00,
            status="Occupied"
        )

    def test_hostel_list_view_and_kpis(self):
        response = self.client.get(reverse('hostel_display'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hostel/dashboard.html')
        self.assertEqual(response.context['total_rooms'], 3)
        self.assertEqual(response.context['occupied_rooms'], 2)
        self.assertEqual(response.context['vacant_rooms'], 1)
        self.assertEqual(float(response.context['total_rent']), 10000.00)

    def test_search_by_student_name(self):
        response = self.client.get(reverse('hostel_display'), {'q': 'Priya'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Priya Patel')
        self.assertNotContains(response, 'Suresh Jadhav')

    def test_search_by_room_no(self):
        response = self.client.get(reverse('hostel_display'), {'q': '201'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suresh Jadhav')
        self.assertNotContains(response, 'Priya Patel')

    def test_filter_by_status(self):
        response = self.client.get(reverse('hostel_display'), {'status': 'Vacant'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '102')
        self.assertNotContains(response, '101')

    def test_filter_by_block(self):
        response = self.client.get(reverse('hostel_display'), {'block': 'Block B'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suresh Jadhav')
        self.assertNotContains(response, 'Priya Patel')

    def test_create_hostel_record(self):
        data = {
            'student_name': 'Neha Deshmukh',
            'room_no': '301',
            'block': 'Block C',
            'floor': 3,
            'warden_name': 'Mrs. Kulkarni',
            'rent': 4800.00,
            'status': 'Occupied',
        }
        response = self.client.post(reverse('hostel_add'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Hostel.objects.filter(room_no='301').exists())

    def test_update_hostel_record(self):
        data = {
            'student_name': 'Priya Patel Updated',
            'room_no': '101',
            'block': 'Block A',
            'floor': 1,
            'warden_name': 'Dr. Patil',
            'rent': 4700.00,
            'status': 'Occupied',
        }
        response = self.client.post(reverse('hostel_edit', kwargs={'pk': self.h1.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.h1.refresh_from_db()
        self.assertEqual(self.h1.student_name, 'Priya Patel Updated')
        self.assertEqual(float(self.h1.rent), 4700.00)

    def test_delete_hostel_record(self):
        response = self.client.post(reverse('hostel_delete', kwargs={'pk': self.h3.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Hostel.objects.filter(pk=self.h3.pk).exists())

    def test_export_hostels_csv(self):
        response = self.client.get(reverse('hostel_export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="hostel_allocations.csv"', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('Student Name,Room No,Block,Floor', content)
        self.assertIn('Priya Patel', content)

    def test_vacate_hostel_room(self):
        response = self.client.post(reverse('hostel_vacate', kwargs={'pk': self.h1.pk}))
        self.assertEqual(response.status_code, 302)
        self.h1.refresh_from_db()
        self.assertEqual(self.h1.status, 'Vacant')
