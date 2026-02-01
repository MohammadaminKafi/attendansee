"""
PDF Report Generation Services

Base classes and implementations for generating various PDF reports
in the attendance system.

Architecture:
- BasePDFService: Abstract base class providing common PDF functionality
- AttendancePDFService: Concrete implementation for attendance reports
- Extensible: Easy to add new report types by inheriting from BasePDFService

Usage Example:
    from .services import AttendancePDFService
    
    pdf_service = AttendancePDFService(class_obj)
    pdf_buffer = pdf_service.generate_report()
    
    # Use in Django view
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    return response

See README_PDF_SERVICES.md for detailed documentation.
"""

from abc import ABC, abstractmethod
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import os

# RTL support for Arabic/Persian text
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    RTL_SUPPORT = True
except ImportError:
    RTL_SUPPORT = False


class BasePDFService(ABC):
    """
    Abstract base class for PDF generation services.
    
    All PDF report generators should inherit from this class and implement
    the generate_report method.
    """
    
    def __init__(self):
        """Initialize the PDF service with common settings."""
        self.buffer = BytesIO()
        self.page_width, self.page_height = letter
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._setup_custom_styles()
    
    def _register_fonts(self):
        """Register UTF-8 compatible fonts for international character support."""
        self.default_font = 'Helvetica'  # Fallback font
        
        # Get the fonts directory path (bundled with the app)
        fonts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'fonts'
        )
        
        # Try multiple font options for Arabic/UTF-8 support
        # First check bundled fonts, then system fonts
        font_paths = [
            os.path.join(fonts_dir, 'Vazirmatn-Regular.ttf'),
            # B Nazanin (highest priority - Persian font)
            os.path.join(fonts_dir, 'B-NAZANIN.TTF'),
            os.path.join(fonts_dir, 'B Nazanin.ttf'),
            '/usr/share/fonts/truetype/BNazanin.ttf',
            '/usr/share/fonts/truetype/B-NAZANIN.TTF',
            # Other bundled fonts
            os.path.join(fonts_dir, 'DejaVuSans.ttf'),
            os.path.join(fonts_dir, 'NotoSansArabic-Regular.ttf'),
            os.path.join(fonts_dir, 'ArialUnicode.ttf'),
            # System fonts (fallback)
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                    self.default_font = 'UnicodeFont'
                    print(f"Successfully loaded font: {font_path}")
                    break
                except Exception as e:
                    print(f"Failed to load font {font_path}: {str(e)}")
                    continue
        
        if self.default_font == 'Helvetica':
            print("WARNING: No Unicode font found. Arabic characters may not render correctly.")
    
    def _process_rtl_text(self, text):
        """
        Process text for RTL (right-to-left) display.
        Handles Arabic and Persian text properly.
        
        Args:
            text: Input text string
            
        Returns:
            str: Processed text ready for RTL display
        """
        if not RTL_SUPPORT or not text:
            return text
        
        # Check if text contains RTL characters (Arabic/Persian range)
        has_rtl = any('\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' 
                      or '\uFB50' <= char <= '\uFDFF' or '\uFE70' <= char <= '\uFEFF'
                      for char in text)
        
        if has_rtl:
            # Reshape Arabic/Persian text (connects letters properly)
            reshaped_text = reshape(text)
            # Apply bidirectional algorithm for proper RTL display
            display_text = get_display(reshaped_text)
            return display_text
        
        return text
    
    def _setup_custom_styles(self):
        """
        Set up custom paragraph styles for the PDF.
        Override this method in subclasses to define custom styles.
        """
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.default_font,
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
    
    @abstractmethod
    def generate_report(self):
        """
        Generate the PDF report.
        
        Returns:
            BytesIO: Buffer containing the PDF data
        """
        pass
    
    def _create_document(self, **kwargs):
        """
        Create a SimpleDocTemplate with standard margins.
        
        Args:
            **kwargs: Additional arguments to pass to SimpleDocTemplate
            
        Returns:
            SimpleDocTemplate: The document template
        """
        return SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=kwargs.get('rightMargin', 0.5*inch),
            leftMargin=kwargs.get('leftMargin', 0.5*inch),
            topMargin=kwargs.get('topMargin', 0.75*inch),
            bottomMargin=kwargs.get('bottomMargin', 0.5*inch)
        )
    
    def _load_image(self, image_path, width=None, height=None):
        """
        Load an image from path with error handling.
        
        Args:
            image_path: Path to the image file
            width: Desired width in inches (optional)
            height: Desired height in inches (optional)
            
        Returns:
            Image or None: ReportLab Image object or None if loading fails
        """
        try:
            if os.path.exists(image_path):
                return Image(image_path, width=width, height=height)
        except Exception as e:
            print(f"Error loading image {image_path}: {str(e)}")
        return None


class AttendancePDFService(BasePDFService):
    """
    Service for generating attendance reports with face crop images.
    
    Generates a PDF showing each student's attendance statistics and
    one face crop image from each attended session.
    """
    
    def __init__(self, class_obj):
        """
        Initialize the attendance PDF service.
        
        Args:
            class_obj: The Class model instance
        """
        super().__init__()
        self.class_obj = class_obj
    
    def _setup_custom_styles(self):
        """Set up custom styles for attendance report."""
        super()._setup_custom_styles()
        
        self.student_header_style = ParagraphStyle(
            'StudentHeader',
            parent=self.styles['Heading2'],
            fontName=self.default_font,
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=8,
            spaceBefore=12
        )
        
        self.session_info_style = ParagraphStyle(
            'SessionInfo',
            parent=self.styles['Normal'],
            fontName=self.default_font,
            fontSize=8,
            textColor=colors.HexColor('#555555'),
            alignment=TA_CENTER
        )
    
    def generate_report(self):
        """
        Generate the complete attendance report PDF.
        
        Returns:
            BytesIO: Buffer containing the PDF data
        """
        # Create the PDF document
        doc = self._create_document()
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add title
        title_text = self._process_rtl_text(f"Attendance Report: {self.class_obj.name}")
        title = Paragraph(
            title_text,
            self.title_style
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Get all students ordered by last name
        students = self.class_obj.students.all().order_by('last_name', 'first_name')
        
        # Get total sessions count
        from ..models import Session
        total_sessions = Session.objects.filter(class_session=self.class_obj).count()
        
        # Process each student
        for idx, student in enumerate(students):
            student_elements = self._generate_student_section(student, total_sessions)
            elements.extend(student_elements)
            
            # Add separator line between students (except for the last one)
            if idx < len(students) - 1:
                elements.append(Spacer(1, 0.2*inch))
                elements.extend(self._create_separator_line())
                elements.append(Spacer(1, 0.2*inch))
        
        # Build the PDF
        doc.build(elements)
        
        # Return buffer at the beginning
        self.buffer.seek(0)
        return self.buffer
    
    def _generate_student_section(self, student, total_sessions):
        """
        Generate the report section for a single student.
        
        Args:
            student: Student model instance
            total_sessions: Total number of sessions in the class
            
        Returns:
            List of reportlab elements for this student
        """
        from ..models import Session, FaceCrop
        
        elements = []
        
        # Get sessions where student was present
        attended_sessions = Session.objects.filter(
            images__face_crops__student=student
        ).distinct().order_by('date', 'created_at')
        
        attended_count = attended_sessions.count()
        attendance_rate = (attended_count / total_sessions * 100) if total_sessions > 0 else 0
        
        # Student header with profile picture and attendance stats
        student_name = self._process_rtl_text(student.full_name)
        header_text = (
            f"{student_name} | "
            f"Presence: {attended_count}/{total_sessions} ({attendance_rate:.0f}%)"
        )
        
        # Create header with profile picture
        if student.profile_picture and student.profile_picture.path and os.path.exists(student.profile_picture.path):
            # Create a table with profile picture on the left and student info on the right
            profile_img = self._load_image(
                student.profile_picture.path,
                width=0.6*inch,
                height=0.6*inch
            )
            
            if profile_img:
                header_paragraph = Paragraph(header_text, self.student_header_style)
                header_table = Table(
                    [[profile_img, header_paragraph]],
                    colWidths=[0.7*inch, self.page_width - 1.7*inch]
                )
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ]))
                elements.append(header_table)
            else:
                # Fallback if image can't be loaded
                header = Paragraph(header_text, self.student_header_style)
                elements.append(header)
        else:
            # No profile picture - just show the text header
            header = Paragraph(header_text, self.student_header_style)
            elements.append(header)
        
        elements.append(Spacer(1, 0.15*inch))
        
        # If student attended no sessions, show message
        if attended_count == 0:
            no_attendance_text = Paragraph(
                "<i>No attendance recorded</i>",
                self.styles['Normal']
            )
            elements.append(no_attendance_text)
            elements.append(Spacer(1, 0.2*inch))
            return elements
        
        # Create image grid for face crops
        image_table = self._create_face_crop_table(student, attended_sessions)
        if image_table:
            elements.append(image_table)
        
        return elements
    
    def _create_face_crop_table(self, student, attended_sessions):
        """
        Create a table containing face crop images with session info.
        
        Args:
            student: Student model instance
            attended_sessions: QuerySet of sessions the student attended
            
        Returns:
            Table or None: ReportLab Table object or None if no images
        """
        from ..models import FaceCrop
        
        image_data = []
        current_row = []
        max_images_per_row = 4
        image_size = 0.9 * inch  # Further reduced from 1.1 to 0.9 inch for tighter spacing
        
        for session in attended_sessions:
            # Get one face crop for this student in this session
            face_crop = FaceCrop.objects.filter(
                image__session=session,
                student=student
            ).first()
            
            if face_crop and face_crop.crop_image_path:
                cell_elements = []
                
                # Try to load and add the face crop image
                img = self._load_image(
                    face_crop.crop_image_path.path,
                    width=image_size,
                    height=image_size
                )
                
                if img:
                    cell_elements.append(img)
                else:
                    # Placeholder if image can't be loaded
                    cell_elements.append(Paragraph(
                        "[Image Not Available]",
                        self.session_info_style
                    ))
                
                # Add session info below image
                session_info = self._create_session_info(session)
                cell_elements.append(session_info)
                
                current_row.append(cell_elements)
                
                # Add row to table when it reaches max images per row
                if len(current_row) == max_images_per_row:
                    image_data.append(current_row)
                    current_row = []
        
        # Add remaining images if any
        if current_row:
            # Fill remaining cells with empty content to maintain structure
            while len(current_row) < max_images_per_row:
                current_row.append('')
            image_data.append(current_row)
        
        # Create table if we have images
        if not image_data:
            return None
        
        # Calculate column widths - use tighter spacing
        available_width = self.page_width - 1*inch
        # Use actual image size plus minimal padding for tighter fit
        col_width = (image_size + 0.15*inch)  # Minimal padding around each image
        
        table = Table(image_data, colWidths=[col_width] * max_images_per_row)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),  # Minimal padding
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),  # Minimal padding
            ('TOPPADDING', (0, 0), (-1, -1), 1),  # Minimal padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Minimal padding
        ]))
        
        return table
    
    def _create_session_info(self, session):
        """
        Create a formatted paragraph with session information.
        
        Args:
            session: Session model instance
            
        Returns:
            Paragraph: ReportLab Paragraph with session details
        """
        session_date = session.date.strftime('%m/%d/%Y')
        session_info_text = f"{session.name}<br/>{session_date}"
        
        if session.start_time:
            session_info_text += f"<br/>{session.start_time.strftime('%H:%M')}"
        
        return Paragraph(session_info_text, self.session_info_style)
    
    def _create_separator_line(self):
        """
        Create a horizontal separator line.
        
        Returns:
            List: List containing a separator line table
        """
        line_data = [['_' * 120]]
        line_table = Table(line_data, colWidths=[self.page_width - 1*inch])
        line_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        return [line_table]
