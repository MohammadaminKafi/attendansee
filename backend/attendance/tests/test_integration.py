import pytest
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from datetime import date, time
from attendance.models import Class, Student, Session, Image, FaceCrop


User = get_user_model()


@pytest.mark.django_db
class TestAttendanceWorkflow:
    """Integration tests for complete attendance workflow."""
    
    def test_complete_attendance_workflow(self, user):
        """Test the complete workflow from class creation to face identification."""
        # 1. Professor creates a class
        cs_class = Class.objects.create(
            owner=user,
            name='Computer Science 101',
            description='Introduction to CS'
        )
        
        # 2. Add students to the class
        student1 = Student.objects.create(
            class_enrolled=cs_class,
            first_name='Alice',
            last_name='Smith',
            student_id='CS001',
            email='alice@example.com'
        )
        student2 = Student.objects.create(
            class_enrolled=cs_class,
            first_name='Bob',
            last_name='Jones',
            student_id='CS002',
            email='bob@example.com'
        )
        
        # 3. Create a session
        session = Session.objects.create(
            class_session=cs_class,
            name='Lecture 1',
            date=date(2025, 10, 22),
            start_time=time(10, 0),
            end_time=time(11, 30)
        )
        
        # 4. Upload images to the session
        image1 = Image.objects.create(
            session=session,
            original_image_path='/uploads/session1_img1.jpg'
        )
        image2 = Image.objects.create(
            session=session,
            original_image_path='/uploads/session1_img2.jpg'
        )
        
        # 5. Process images and create face crops
        image1.mark_as_processed('/processed/session1_img1.jpg')
        
        crop1 = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/crops/crop1.jpg',
            coordinates='100,100,150,150'
        )
        crop2 = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/crops/crop2.jpg',
            coordinates='300,100,150,150'
        )
        
        # 6. Identify students in crops
        crop1.identify_student(student1, confidence=0.95)
        crop2.identify_student(student2, confidence=0.89)
        
        # Verify the complete workflow
        assert cs_class.students.count() == 2
        assert cs_class.sessions.count() == 1
        assert session.images.count() == 2
        assert image1.face_crops.count() == 2
        assert student1.face_crops.count() == 1
        assert student2.face_crops.count() == 1
        
        # Check processing status
        assert image1.is_processed is True
        assert image2.is_processed is False
        session.refresh_from_db()
        assert session.is_processed is False  # Not all images processed
        
        # Process second image
        image2.mark_as_processed('/processed/session1_img2.jpg')
        session.refresh_from_db()
        assert session.is_processed is True  # All images processed
    
    def test_attendance_tracking_multiple_sessions(self, user):
        """Test tracking attendance across multiple sessions."""
        cs_class = Class.objects.create(owner=user, name='CS 101')
        
        # Create students
        alice = Student.objects.create(
            class_enrolled=cs_class,
            first_name='Alice',
            last_name='Brown'
        )
        bob = Student.objects.create(
            class_enrolled=cs_class,
            first_name='Bob',
            last_name='Green'
        )
        
        # Create multiple sessions
        session1 = Session.objects.create(
            class_session=cs_class,
            name='Week 1',
            date=date(2025, 10, 15)
        )
        session2 = Session.objects.create(
            class_session=cs_class,
            name='Week 2',
            date=date(2025, 10, 22)
        )
        
        # Session 1: Both students present
        img1 = Image.objects.create(
            session=session1,
            original_image_path='/img1.jpg'
        )
        img1.mark_as_processed('/proc1.jpg')
        
        crop1 = FaceCrop.objects.create(
            image=img1,
            crop_image_path='/crop1.jpg',
            coordinates='0,0,100,100'
        )
        crop1.identify_student(alice)
        
        crop2 = FaceCrop.objects.create(
            image=img1,
            crop_image_path='/crop2.jpg',
            coordinates='100,0,100,100'
        )
        crop2.identify_student(bob)
        
        # Session 2: Only Alice present
        img2 = Image.objects.create(
            session=session2,
            original_image_path='/img2.jpg'
        )
        img2.mark_as_processed('/proc2.jpg')
        
        crop3 = FaceCrop.objects.create(
            image=img2,
            crop_image_path='/crop3.jpg',
            coordinates='0,0,100,100'
        )
        crop3.identify_student(alice)
        
        # Verify attendance tracking
        alice_attendance = alice.face_crops.count()
        bob_attendance = bob.face_crops.count()
        
        assert alice_attendance == 2  # Present in both sessions
        assert bob_attendance == 1    # Present in one session
        
        # Check which sessions each student attended
        alice_sessions = Session.objects.filter(
            images__face_crops__student=alice
        ).distinct()
        bob_sessions = Session.objects.filter(
            images__face_crops__student=bob
        ).distinct()
        
        assert alice_sessions.count() == 2
        assert bob_sessions.count() == 1
    
    def test_unidentified_faces_handling(self, user):
        """Test handling of unidentified faces in images."""
        cs_class = Class.objects.create(owner=user, name='CS 101')
        alice = Student.objects.create(
            class_enrolled=cs_class,
            first_name='Alice',
            last_name='White'
        )
        
        session = Session.objects.create(
            class_session=cs_class,
            name='Lecture',
            date=date.today()
        )
        
        image = Image.objects.create(
            session=session,
            original_image_path='/img.jpg'
        )
        image.mark_as_processed('/proc.jpg')
        
        # Create identified and unidentified crops
        identified_crop = FaceCrop.objects.create(
            image=image,
            crop_image_path='/crop1.jpg',
            coordinates='0,0,100,100'
        )
        identified_crop.identify_student(alice)
        
        unidentified_crop = FaceCrop.objects.create(
            image=image,
            crop_image_path='/crop2.jpg',
            coordinates='100,0,100,100'
        )
        
        # Query identified vs unidentified faces
        identified = image.face_crops.filter(is_identified=True)
        unidentified = image.face_crops.filter(is_identified=False)
        
        assert identified.count() == 1
        assert unidentified.count() == 1
        assert identified.first().student == alice
        assert unidentified.first().student is None


@pytest.mark.django_db
class TestComplexQueries:
    """Test complex database queries for analytics."""
    
    def test_class_statistics(self, user):
        """Test getting statistics for a class."""
        cs_class = Class.objects.create(owner=user, name='CS 101')
        
        # Create students
        for i in range(5):
            Student.objects.create(
                class_enrolled=cs_class,
                first_name=f'Student{i}',
                last_name='Test'
            )
        
        # Create sessions
        for i in range(3):
            Session.objects.create(
                class_session=cs_class,
                name=f'Week {i+1}',
                date=date(2025, 10, 15 + i * 7)
            )
        
        # Get statistics
        assert cs_class.students.count() == 5
        assert cs_class.sessions.count() == 3
    
    def test_student_attendance_rate(self, user):
        """Test calculating student attendance rate."""
        cs_class = Class.objects.create(owner=user, name='CS 101')
        alice = Student.objects.create(
            class_enrolled=cs_class,
            first_name='Alice',
            last_name='Test'
        )
        
        # Create 3 sessions
        sessions = []
        for i in range(3):
            sessions.append(Session.objects.create(
                class_session=cs_class,
                name=f'Week {i+1}',
                date=date(2025, 10, 15 + i * 7)
            ))
        
        # Alice attends 2 out of 3 sessions
        for i in [0, 2]:
            img = Image.objects.create(
                session=sessions[i],
                original_image_path=f'/img{i}.jpg'
            )
            img.mark_as_processed(f'/proc{i}.jpg')
            
            crop = FaceCrop.objects.create(
                image=img,
                crop_image_path=f'/crop{i}.jpg',
                coordinates='0,0,100,100'
            )
            crop.identify_student(alice)
        
        # Calculate attendance
        sessions_attended = Session.objects.filter(
            images__face_crops__student=alice
        ).distinct().count()
        
        total_sessions = cs_class.sessions.count()
        attendance_rate = sessions_attended / total_sessions if total_sessions > 0 else 0
        
        assert sessions_attended == 2
        assert total_sessions == 3
        assert attendance_rate == pytest.approx(0.667, rel=0.01)
    
    def test_session_attendance_summary(self, user):
        """Test getting attendance summary for a session."""
        cs_class = Class.objects.create(owner=user, name='CS 101')
        
        students = []
        for i in range(4):
            students.append(Student.objects.create(
                class_enrolled=cs_class,
                first_name=f'Student{i}',
                last_name='Test'
            ))
        
        session = Session.objects.create(
            class_session=cs_class,
            name='Week 1',
            date=date.today()
        )
        
        image = Image.objects.create(
            session=session,
            original_image_path='/img.jpg'
        )
        image.mark_as_processed('/proc.jpg')
        
        # 3 students present, 1 absent
        for i in range(3):
            crop = FaceCrop.objects.create(
                image=image,
                crop_image_path=f'/crop{i}.jpg',
                coordinates=f'{i*100},0,100,100'
            )
            crop.identify_student(students[i])
        
        # Get attendance summary
        present_students = Student.objects.filter(
            face_crops__image__session=session
        ).distinct()
        
        total_students = cs_class.students.count()
        present_count = present_students.count()
        absent_count = total_students - present_count
        
        assert total_students == 4
        assert present_count == 3
        assert absent_count == 1
    
    def test_professor_classes_with_counts(self, user, another_user):
        """Test getting classes with related object counts."""
        # User 1 creates 2 classes
        class1 = Class.objects.create(owner=user, name='CS 101')
        class2 = Class.objects.create(owner=user, name='Math 101')
        
        # User 2 creates 1 class
        class3 = Class.objects.create(owner=another_user, name='Physics 101')
        
        # Add students to class1
        for i in range(3):
            Student.objects.create(
                class_enrolled=class1,
                first_name=f'Student{i}',
                last_name='Test'
            )
        
        # Add sessions to class1
        for i in range(2):
            Session.objects.create(
                class_session=class1,
                name=f'Week {i+1}',
                date=date(2025, 10, 15 + i * 7)
            )
        
        # Query with annotations
        user_classes = Class.objects.filter(owner=user).annotate(
            student_count=Count('students', distinct=True),
            session_count=Count('sessions', distinct=True)
        )
        
        assert user_classes.count() == 2
        
        class1_annotated = user_classes.get(id=class1.id)
        assert class1_annotated.student_count == 3
        assert class1_annotated.session_count == 2
        
        class2_annotated = user_classes.get(id=class2.id)
        assert class2_annotated.student_count == 0
        assert class2_annotated.session_count == 0


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_session_with_no_images(self, session1):
        """Test session processing status with no images."""
        session1.update_processing_status()
        assert session1.is_processed is False
    
    def test_image_with_no_face_crops(self, image1):
        """Test image with no detected faces."""
        assert image1.face_crops.count() == 0
        image1.mark_as_processed('/proc.jpg')
        assert image1.is_processed is True
    
    def test_multiple_crops_same_student(self, image1, student1):
        """Test multiple face crops for the same student in one image."""
        crop1 = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/crop1.jpg',
            coordinates='0,0,100,100'
        )
        crop1.identify_student(student1)
        
        crop2 = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/crop2.jpg',
            coordinates='100,0,100,100'
        )
        crop2.identify_student(student1)
        
        # Should have 2 crops for the same student
        assert student1.face_crops.count() == 2
        assert image1.face_crops.filter(student=student1).count() == 2
    
    def test_empty_class(self, test_class):
        """Test class with no students or sessions."""
        assert test_class.students.count() == 0
        assert test_class.sessions.count() == 0
    
    def test_archived_class_behavior(self, inactive_class):
        """Test that inactive classes still function normally."""
        assert inactive_class.is_active is False
        
        # Should still be able to add students and sessions
        student = Student.objects.create(
            class_enrolled=inactive_class,
            first_name='Test',
            last_name='Student'
        )
        session = Session.objects.create(
            class_session=inactive_class,
            name='Test Session',
            date=date.today()
        )
        
        assert inactive_class.students.count() == 1
        assert inactive_class.sessions.count() == 1
    
    def test_coordinates_with_spaces(self, image1):
        """Test parsing coordinates with extra whitespace."""
        crop = FaceCrop.objects.create(
            image=image1,
            crop_image_path='/crop.jpg',
            coordinates=' 100 , 150 , 200 , 250 '
        )
        
        coords = crop.parse_coordinates()
        assert coords == {
            'x': 100,
            'y': 150,
            'width': 200,
            'height': 250
        }
    
    def test_reassign_face_crop_to_different_student(self, face_crop1, student1, student2):
        """Test changing the student assignment of a face crop."""
        assert face_crop1.student == student1
        
        face_crop1.identify_student(student2, confidence=0.97)
        
        face_crop1.refresh_from_db()
        assert face_crop1.student == student2
        assert face_crop1.confidence_score == 0.97
    
    def test_very_long_names(self, test_class):
        """Test handling of maximum length names."""
        long_name = 'A' * 150  # Max length is 150
        student = Student.objects.create(
            class_enrolled=test_class,
            first_name=long_name,
            last_name=long_name
        )
        
        assert len(student.first_name) == 150
        assert len(student.last_name) == 150
        assert student.full_name == f"{long_name} {long_name}"
    
    def test_special_characters_in_paths(self, session1):
        """Test handling of special characters in file paths."""
        special_path = "/path/with spaces/and-dashes/file (1).jpg"
        image = Image.objects.create(
            session=session1,
            original_image_path=special_path
        )
        
        assert image.original_image_path == special_path
