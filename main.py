# imports
from PIL import Image
from PyPDF2 import PdfWriter, PdfReader
from colorama import init, Fore, Style
from dotenv import load_dotenv
from io import BytesIO
import aiohttp
import asyncio
import logging
import os
import ssl

# init
load_dotenv(dotenv_path='utils/.env')
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
init(autoreset=True)

BASE_URL = "https://www.webassign.net/ebooks/kaufacs10/docs/KaufACS10.pdf_{}.jpg"
OUTPUT_PDF = "output.pdf"
MAX_CONCURRENT_REQUESTS = 100

COOKIES = {
    'dtCookie': os.getenv('DTCOOKIE'),
    'seen_student_memo': os.getenv('SEEN_STUDENT_MEMO'),
    'cmp-session-id': os.getenv('CMP_SESSION_ID'),
    'UserPass': os.getenv('USERPASS'),
    'kaufacs10': os.getenv('KAUFACS10'),
    'QSI_HistorySession': os.getenv('QSI_HISTORYSESSION')
}
async def download_image(session, page_num):
    url = BASE_URL.format(page_num)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with session.get(url, cookies=COOKIES, ssl=ssl_context) as response:
        if response.status == 200:
            logging.info(f"{Fore.YELLOW}Downloading image for page {page_num}{Style.RESET_ALL}")
            return await response.read()
        return None

async def process_pages():
    page_num = 1
    pdf_writer = PdfWriter()
    output_pdf = "export.pdf"
    
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [download_image(session, i) for i in range(page_num, page_num + MAX_CONCURRENT_REQUESTS)]
            results = await asyncio.gather(*tasks)
            
            if all(result is None for result in results):
                logging.info(f"{Fore.RED}No more pages to process. Exiting.{Style.RESET_ALL}")
                break
            
            for result in results:
                if result:
                    logging.info(f"{Fore.YELLOW}Processing page {page_num}{Style.RESET_ALL}")
                    image = Image.open(BytesIO(result))
                    
                    pdf_bytes = BytesIO()
                    image.save(pdf_bytes, format='PDF')
                    pdf_bytes.seek(0)
                    
                    pdf_reader = PdfReader(pdf_bytes)
                    page = pdf_reader.pages[0]
                    
                    pdf_writer.add_page(page)
                    
                    with open(output_pdf, "wb") as output_file:
                        pdf_writer.write(output_file)
                    
                    logging.info(f"{Fore.GREEN}Added page {page_num} to {output_pdf}{Style.RESET_ALL}")
                
                page_num += 1
            
            logging.info(f"{Fore.YELLOW}Processed up to page {page_num - 1}{Style.RESET_ALL}")

    logging.info(f"{Fore.CYAN}Finished processing all pages. Final PDF saved as {output_pdf}.{Style.RESET_ALL}")

if __name__ == "__main__":
    logging.info(f"{Fore.CYAN}Starting the PDF compilation process{Style.RESET_ALL}")
    asyncio.run(process_pages())
    logging.info(f"{Fore.CYAN}PDF compilation process completed.{Style.RESET_ALL}")