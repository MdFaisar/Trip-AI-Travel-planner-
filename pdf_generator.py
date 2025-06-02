from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import tempfile
import os
from datetime import datetime
import re

class NumberedCanvas(canvas.Canvas):
    """Custom canvas class to add page numbers and headers/footers"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
    
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        num_pages = len(self._saved_page_states)
        for (page_num, page_state) in enumerate(self._saved_page_states):
            self.__dict__.update(page_state)
            self.draw_page_number(page_num + 1, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    
    def draw_page_number(self, page_num, total_pages):
        """Draw page number and header/footer"""
        self.setFont("Helvetica", 9)
        
        # Header
        self.setFillColor(colors.HexColor('#2E86AB'))
        self.line(50, letter[1] - 50, letter[0] - 50, letter[1] - 50)
        self.drawString(50, letter[1] - 35, "TripAI - Your Personal Travel Planner")
        
        # Footer
        self.setFillColor(colors.grey)
        self.line(50, 50, letter[0] - 50, 50)
        
        # Page number
        self.drawRightString(letter[0] - 50, 35, f"Page {page_num} of {total_pages}")
        
        # Generation date
        self.drawString(50, 35, f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")

class TripPDFGenerator:
    """Generate PDF reports for trip plans"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self._register_fonts()
    
    def _register_fonts(self):
        """Register custom fonts if available"""
        try:
            # Try to register a Unicode font for better character support
            font_path = os.path.join('assets', 'Arial Unicode.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial Unicode', font_path))
        except Exception:
            # Fallback to built-in fonts
            pass
    
    def _setup_styles(self):
        """Setup custom styles for the PDF"""
        
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB'),
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#A23B72'),
            fontName='Helvetica-Bold'
        )
        
        # Section heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#F18F01'),
            backColor=colors.HexColor('#FFF8E1'),
            borderPadding=8,
            fontName='Helvetica-Bold',
            borderRadius=5
        )
        
        # Subheading style
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#C73E1D'),
            fontName='Helvetica-Bold'
        )
        
        # Body text style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leading=14,
            fontName='Helvetica'
        )
        
        # Bullet point style
        self.bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leftIndent=20,
            bulletIndent=15,
            leading=12,
            fontName='Helvetica'
        )
        
        # Important note style
        self.important_style = ParagraphStyle(
            'ImportantNote',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.HexColor('#D32F2F'),
            backColor=colors.HexColor('#FFEBEE'),
            borderPadding=8,
            fontName='Helvetica-Bold'
        )
    
    def _parse_content(self, content):
        """Parse trip content and structure it"""
        sections = []
        current_section = {'title': '', 'content': '', 'type': 'normal'}
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for various heading patterns
            is_heading = False
            
            # Pattern 1: All caps or with special chars
            if (re.match(r'^[A-Z\s&\-:]+:?\s*$', line) and len(line) > 3) or \
               re.match(r'^\*\*.*\*\*$', line) or \
               re.match(r'^#+\s', line) or \
               re.match(r'^DAY\s+\d+', line, re.IGNORECASE) or \
               re.match(r'^OVERVIEW|^ITINERARY|^BUDGET|^RECOMMENDATIONS|^TIPS|^TRANSPORTATION|^ACCOMMODATION', line, re.IGNORECASE):
                is_heading = True
            
            if is_heading:
                # Save previous section
                if current_section['content'] or current_section['title']:
                    sections.append(current_section)
                
                # Start new section
                title = line.replace('*', '').replace('#', '').strip(':').title()
                current_section = {
                    'title': title,
                    'content': '',
                    'type': 'section'
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add last section
        if current_section['content'] or current_section['title']:
            sections.append(current_section)
        
        return sections
    
    def _format_section_content(self, content):
        """Format section content into flowables"""
        flowables = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for different content types
            if re.match(r'^\d+\.', line):
                # Numbered list item
                text = re.sub(r'^\d+\.\s*', '• ', line)
                text = self._format_text(text)
                flowables.append(Paragraph(text, self.bullet_style))
                
            elif line.startswith('- ') or line.startswith('• '):
                # Bullet point
                text = re.sub(r'^[-•]\s*', '• ', line)
                text = self._format_text(text)
                flowables.append(Paragraph(text, self.bullet_style))
                
            elif re.match(r'^[A-Z\s]+:', line) or line.startswith('##'):
                # Subheading
                text = line.replace('#', '').strip(':')
                flowables.append(Paragraph(text, self.subheading_style))
                
            elif 'important' in line.lower() or 'note:' in line.lower() or 'warning:' in line.lower():
                # Important note
                text = self._format_text(line)
                flowables.append(Paragraph(text, self.important_style))
                
            else:
                # Regular paragraph
                text = self._format_text(line)
                if text:
                    flowables.append(Paragraph(text, self.body_style))
        
        return flowables
    
    def _format_text(self, text):
        """Apply text formatting"""
        # Handle bold formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Handle italic formatting
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Handle currency symbols
        text = text.replace('₹', '₹')
        text = text.replace('$', '$')
        text = text.replace('€', '€')
        
        return text
    
    def _create_summary_table(self, start_location, destination, start_date, end_date, budget=None):
        """Create a summary table with trip details"""
        duration = (end_date - start_date).days + 1
        
        data = [
            ['Trip Summary', ''],
            ['From:', start_location],
            ['To:', destination],
            ['Start Date:', start_date.strftime('%B %d, %Y (%A)')],
            ['End Date:', end_date.strftime('%B %d, %Y (%A)')],
            ['Duration:', f"{duration} days"],
        ]
        
        if budget:
            budget_text = f"{budget.get('symbol', '₹')}{budget.get('amount', 0):,.0f} {budget.get('currency', 'INR')}"
            data.append(['Budget:', budget_text])
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F0F8FF')),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        return table
    
    def generate_pdf(self, trip_plan, start_location, destination, start_date, end_date, budget=None):
        """Generate PDF for trip plan"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        # Create PDF document with custom canvas
        doc = SimpleDocTemplate(
            temp_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=100,  # Extra space for header
            bottomMargin=100  # Extra space for footer
        )
        
        # Build document content
        story = []
        
        # Title
        story.append(Paragraph(
            f"Trip Plan: {start_location} ✈ {destination}",
            self.title_style
        ))
        
        story.append(Spacer(1, 20))
        
        # Trip summary table
        summary_table = self._create_summary_table(start_location, destination, start_date, end_date, budget)
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Parse and add trip content
        sections = self._parse_content(trip_plan)
        
        for i, section in enumerate(sections):
            if section['title']:
                story.append(Paragraph(section['title'], self.heading_style))
                story.append(Spacer(1, 10))
            
            # Format section content
            if section['content']:
                content_flowables = self._format_section_content(section['content'])
                story.extend(content_flowables)
            
            # Add spacing between sections
            if i < len(sections) - 1:
                story.append(Spacer(1, 20))
        
        # Add disclaimer
        story.append(Spacer(1, 30))
        disclaimer = """
        <b>Disclaimer:</b> This trip plan is generated by AI and serves as a general guide. 
        Prices, availability, and information may vary. Please verify all details before making 
        any bookings or travel arrangements. Have a wonderful trip!
        """
        story.append(Paragraph(disclaimer, self.important_style))
        
        # Build PDF with custom canvas
        doc.build(story, canvasmaker=NumberedCanvas)
        
        return temp_path

def generate_trip_pdf(trip_plan, start_location, destination, start_date, end_date, budget=None):
    """Convenience function to generate trip PDF"""
    generator = TripPDFGenerator()
    return generator.generate_pdf(trip_plan, start_location, destination, start_date, end_date, budget)