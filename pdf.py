import os
import re
import json
from PyPDF2 import PdfReader, PdfWriter
import platform
from progress_status import ProgressStatus

if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl

class PDF:
    filename = ''
    file_pages = ''
    
    def __init__(self, filename: str = ''):
        self.filename = filename
        self.file_pages = self.filename + ".pages"
        self.settings_file = self.filename + ".settings"

    def load_search_pattern(self) -> str:
        """
        Load the search pattern from settings_file

        Returns:
            str: The search pattern to be used for extracting account numbers.
        """
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                search_pattern = settings.get("search_pattern", r'Account:\\b(\\d+)')
        else:
            search_pattern = os.getenv("search_pattern", r'Account:\\b(\\d+)')
        return search_pattern


    def process_pdf(self) -> dict:
        """
        Process a PDF file by determining its size and identifying page numbers
        where account numbers (a sequence of 5 or more digits) are visible.
        
        Args:
            self.filename: Path to the PDF file.
            
        Returns:
            A dictionary with processing results, including file size and page numbers.
        """
        if not os.path.exists(self.filename):
            return {"error": f"File '{self.filename}' does not exist."}
        
        file_size = os.path.getsize(self.filename)

        self.remove_pages_file()

        ps = ProgressStatus(upload_folder=os.getenv('UPLOAD_FOLDER'), filename=self.filename)

        # Extract account number pages using a regex to match numbers with 5+ digits.
        try:
            reader = PdfReader(self.filename)
            current_page = 0
            last_page = len(reader.pages)
            ps.set_max(last_page)
            ps.set_current(0)

            account_pages = []
            search_pattern = self.load_search_pattern()
            pattern = re.compile(search_pattern)
            for i, page in enumerate(reader.pages, start=1):
                ps.set_current(i)
                text = page.extract_text() or ""
                match = pattern.search(text)
                if match:
                    account = match.group(1)
                else:
                    account = None
                if account is not None:
                    account_pages.append({"account": account, "page":i})
                    print(f"Page:{i}, Account:{account}", end="\r")
        except Exception as e:
            return {"error": f"Error processing PDF: {str(e)}"}
        
        # determine minimum and maximum page numbers for each account number.
        account_ranges = []
        if account_pages:
            current_account = account_pages[0]["account"]
            page_start = account_pages[0]["page"]
            page_end = account_pages[0]["page"]

            for entry in account_pages[1:]:
                if entry["account"] == current_account:
                    page_end = entry["page"]
                else:
                    account_ranges.append({
                        "account": current_account,
                        "page_start": page_start,
                        "page_end": page_end
                    })
                    current_account = entry["account"]
                    page_start = entry["page"]
                    page_end = entry["page"]

            # Append the last account range
            account_ranges.append({
                "account": current_account,
                "page_start": page_start,
                "page_end": page_end
            })

            ps = None  # Clear the progress status after processing

        # for entry in account_ranges:
        #     entry['target'] = self.calculate_target_folder(entry['account'])

        # save the account pages to a file
        with open(self.file_pages, "w") as f:
            json.dump(account_ranges, f, indent=4)
        
        return {
            "info": f"Processed PDF '{os.path.basename(self.filename)}' with size {file_size} bytes.",
            "account_ranges": account_ranges
        }



    def calculate_target_folder(self, account ) -> str:
        filepath = ''
        base_folder = os.environ.get("BASE_FOLDER", "./")
        # convert account to a 10 digit zero padded string
        account = f"{int(account):010}"
        # split the account number into 5 groups of 2 digits with '/' separator
        parts = [account[i:i+2] for i in range(0, len(account), 2)]
        # join the parts with '/' separator
        folder = "/".join(parts)
        # create the target folder path
        filepath = os.path.join(base_folder, folder)
        return filepath

    def process_pdf_test(self) -> dict:
        if not os.path.exists(self.filename):
            return {"error": f"File '{self.filename}' does not exist."}

        # Extract account number pages using a regex to match numbers with 5+ digits.
        try:
            reader = PdfReader(self.filename)
            search_pattern = self.load_search_pattern()
            pattern = re.compile(search_pattern)
            account1 = None; page1 = None
            account2 = None; page2 = None
            for i, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                match = pattern.search(text)
                if match:
                    account = match.group(1)
                else:
                    account = None

                if account is not None:
                    if account1 is None:
                        account1 = account
                        page1 = i
                    elif account2 is None:
                        account2 = account
                        page2 = i
                    else:
                        # If both accounts are found, save to test_file and break
                        test_file = self.filename + ".test.pdf"
                        # extract pages for page1 to (page2-1)
                        with open(test_file, "wb") as f_out:
                            writer = PdfWriter()

                            for j in range(page1,page2):
                                onepage = reader.pages[j]
                                writer.add_page(onepage)
                            writer.write(f_out)
                            writer.close()
                        break
        except Exception as e:
            return {"error": f"Error processing PDF: {str(e)}"}

        return {
            "info": f"Test PDF '{os.path.basename(self.filename)}/{self.filename}.test.pdf'",
            "page1": page1,
            "page2": page2,
        }

    def remove_pages_file(self):
        rslt = False
        if os.path.exists(self.file_pages):
            os.remove(self.file_pages)
            rslt = True
        return rslt
    
