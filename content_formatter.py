import re
import markdown
from bs4 import BeautifulSoup

class TripContentFormatter:
    """
    A class to format AI-generated trip content for better web display
    """
    
    def __init__(self):
        # Fixed: Removed invalid extension_configs for nl2br
        self.markdown_processor = markdown.Markdown(
            extensions=['tables', 'fenced_code', 'nl2br']
        )
    
    def format_for_web(self, content):
        """
        Format trip content for web display with proper HTML structure
        """
        if not content:
            return ""
        
        # Clean and preprocess the content
        formatted_content = self._preprocess_content(content)
        
        # Apply markdown formatting
        html_content = self.markdown_processor.convert(formatted_content)
        
        # Post-process HTML for better styling
        html_content = self._post_process_html(html_content)
        
        return html_content
    
    def _preprocess_content(self, content):
        """
        Preprocess content to ensure proper markdown formatting
        """
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append('')
                continue
            
            # Format day headers
            if re.match(r'^(Day \d+|DAY \d+)', line, re.IGNORECASE):
                line = f"## {line}"
            
            # Format section headers (lines ending with colon)
            elif line.endswith(':') and not any(char.isdigit() for char in line.split(':')[0]):
                # Check if it's not a time format
                if not re.match(r'^\d{1,2}:\d{2}', line):
                    line = f"### {line}"
            
            # Format bullet points
            elif line.startswith(('•', '-', '*', '+')):
                line = re.sub(r'^[•\-\*\+]\s*', '- ', line)
            
            # Format numbered lists
            elif re.match(r'^\d+[\.\)]\s', line):
                line = re.sub(r'^(\d+)[\.\)]\s', r'\1. ', line)
            
            # Format important notes or tips
            elif any(keyword in line.lower() for keyword in ['note:', 'tip:', 'important:', 'warning:']):
                line = f"**{line}**"
            
            # Format time ranges and costs
            elif re.search(r'\d{1,2}:\d{2}|\₹|\$|€|£', line):
                line = f"*{line}*"
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _post_process_html(self, html_content):
        """
        Post-process HTML content for better styling and structure
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Add CSS classes to elements
        for h2 in soup.find_all('h2'):
            h2['class'] = 'day-header'
        
        for h3 in soup.find_all('h3'):
            h3['class'] = 'section-header'
        
        for ul in soup.find_all('ul'):
            ul['class'] = 'trip-list'
        
        for ol in soup.find_all('ol'):
            ol['class'] = 'numbered-list'
        
        for em in soup.find_all('em'):
            em['class'] = 'time-cost-info'
        
        for strong in soup.find_all('strong'):
            strong['class'] = 'important-note'
        
        # Add structure divs
        content_sections = []
        current_section = []
        
        for element in soup.children:
            if element.name == 'h2':  # Day header
                if current_section:
                    section_div = soup.new_tag('div', **{'class': 'day-section'})
                    for item in current_section:
                        section_div.append(item)
                    content_sections.append(section_div)
                    current_section = []
                current_section.append(element)
            else:
                current_section.append(element)
        
        # Add the last section
        if current_section:
            section_div = soup.new_tag('div', **{'class': 'day-section'})
            for item in current_section:
                section_div.append(item)
            content_sections.append(section_div)
        
        # Rebuild the soup with sections
        soup.clear()
        for section in content_sections:
            soup.append(section)
        
        return str(soup)
    
    def extract_summary(self, content, max_length=200):
        """
        Extract a summary from the trip content
        """
        if not content:
            return ""
        
        # Remove markdown and HTML tags
        clean_content = re.sub(r'[#*_`]', '', content)
        clean_content = BeautifulSoup(clean_content, 'html.parser').get_text()
        
        # Get first meaningful paragraph
        paragraphs = [p.strip() for p in clean_content.split('\n') if p.strip() and len(p.strip()) > 50]
        
        if paragraphs:
            summary = paragraphs[0]
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            return summary
        
        return "Trip plan generated successfully"
    
    def get_day_wise_content(self, content):
        """
        Split content into day-wise sections
        """
        if not content:
            return []
        
        # Split by day headers
        days = re.split(r'(?=^(?:Day|DAY)\s+\d+)', content, flags=re.MULTILINE)
        
        day_contents = []
        for day in days:
            day = day.strip()
            if day:
                lines = day.split('\n')
                if lines:
                    title = lines[0].strip()
                    content_lines = lines[1:] if len(lines) > 1 else []
                    content_text = '\n'.join(content_lines).strip()
                    
                    day_contents.append({
                        'title': title,
                        'content': content_text,
                        'formatted_content': self.format_for_web(content_text)
                    })
        
        return day_contents
    
    def format_for_pdf(self, content):
        """
        Format content specifically for PDF generation (keeps original logic)
        """
        # This maintains compatibility with existing PDF generator
        return content
    
    def get_highlights(self, content):
        """
        Extract key highlights from the trip content
        """
        highlights = []
        
        if not content:
            return highlights
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for important attractions, activities, or recommendations
            if any(keyword in line.lower() for keyword in [
                'must visit', 'recommended', 'famous for', 'highlight', 
                'don\'t miss', 'popular', 'attraction', 'landmark'
            ]):
                clean_line = re.sub(r'^[•\-\*\+]\s*', '', line)
                clean_line = re.sub(r'[#*_`]', '', clean_line)
                if len(clean_line) > 20:
                    highlights.append(clean_line)
        
        return highlights[:5]  # Return top 5 highlights