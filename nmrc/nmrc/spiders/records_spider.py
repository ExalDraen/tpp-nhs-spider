import scrapy
from ..secrets import USER, PASSWORD


class RecordsSpider(scrapy.Spider):
    """
    Spider for crawling and extracting the tabular patient records available via the systmonline tpp site,
    as used by the NHS in the UK.
    """
    name = 'medical_records'
    start_url = 'https://systmonline.tpp-uk.com/2/Login'
    start_urls=[start_url]
    start_date = '28/03/2003'
    end_date = '28/03/2018'

    def parse(self, response):
        self.logger.info("Starting scrape after initial response at %s", response.url)
        self.logger.debug("Response Headers: %s", response.headers)

        next_req = scrapy.FormRequest.from_response(
            response=response,
            formdata={'Username': USER, 'Password': PASSWORD, 'Login': ''},
            formcss='form[action="Login"]',
            callback=self.logged_in)
        self.logger.debug("Next req will have URL: %s, Cookies: %s", next_req.url, next_req.cookies)

        return [next_req]

    def logged_in(self, response: scrapy.http.Response) -> scrapy.Request:
        self.logger.info("Continuing scrape post-login")
        self.logger.debug("Headers: %s", response.headers)

        # Extra form data to get the full range of patient data;
        #  probably not necessary for this initial request.
        form_data = {
                     'DateFrom': self.start_date,
                     'DateTo': self.end_date,
                     'IncludeUnknownDates': 'on',
                    }

        next_req = scrapy.FormRequest.from_response(
                response=response,
                formcss='form[action="PatientRecord"]',
                formdata=form_data,
                callback=self.fan_out,
                )

        self.logger.debug("Next req will have URL: %s", next_req.url)

        return next_req

    def fan_out(self, response: scrapy.http.Response) -> scrapy.Request:
        """
        Scrape each of the patient record detail pages present in the response. Yields a new request per detail page.
        :param response: Response for the patient record detail page
        """
        self.logger.info("Fanning out requests from %s", response.url)

        # The number of pages is not returned in any useful format so we have to extract it by finding the
        # penultimate page link (the last one is "next")
        last_page = response.xpath("//form[@name='FormRecordFilters']/p/a[last()-1]/text()").extract_first()
        self.logger.debug("Last page number is %s", last_page)
        last_page = int(last_page)
        
        for i in range(1, last_page):
            # To get page X from the Record filter we need to send a PageX=PageX key in its POST data.
            page = f'Page{i}'
            form_data = {
                         'DateFrom': self.start_date,
                         'DateTo': self.end_date,
                         'IncludeUnknownDates': 'on',
                         page: page,
                        }
            self.logger.debug("Form data: %s", form_data)

            next_req = scrapy.FormRequest.from_response(
                    response=response,
                    formcss='form[action="PatientRecord"]',
                    formdata=form_data,
                    callback=self.dump,
                    meta={"page": i},
                    )
            yield next_req

    def dump(self, response: scrapy.http.Response):
        page_num = response.meta.get("page")
        self.logger.info("Dumping data from %s, page number: %s", response.url, page_num)

        out_path = f"output/patient_record_{page_num:02d}.html"

        # Dump the table containing the actual patient records.
        with open(out_path, "wt", encoding="UTF8") as f:
            f.write(response.xpath("//table[@id='patientRecord']").extract_first())
