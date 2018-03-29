import scrapy
from scrapy.utils.response import open_in_browser
from ..secrets import USER, PASSWORD


class RecordsSpider(scrapy.Spider):
    name = 'medical_records'
    start_url = 'https://systmonline.tpp-uk.com/2/Login'
    start_urls=[start_url]
    patient_url = 'https://systmonline.tpp-uk.com/2/PatientRecord'
    start_date = '28/03/2003'
    end_date = '28/03/2018'
    endDate = ''

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
        self.logger.info("Continuing scrape with %s", self.patient_url)
        self.logger.debug("Headers: %s", response.headers)

        uuid = response.xpath("//form/input[@name='UUID']/@value").extract_first()
        self.logger.debug("Found UUID: %s", uuid)
        if not uuid:
            open_in_browser(response)

        form_data = {
                      #'UUID': uuid,
                     'DateFrom': self.start_date,
                     'DateTo': self.end_date,
                     'IncludeUnknownDates': 'on',
                     'Page1': 'Page1'
                    }

        next_req = scrapy.FormRequest.from_response(
                response=response,
                #url=self.patient_url,
                formcss='form[action="PatientRecord"]',
                formdata=form_data,
                callback=self.fan_out,
                )

        self.logger.debug("Next req will have URL: %s, Cookies: %s", next_req.url, next_req.cookies)

        return next_req

    def fan_out(self, response: scrapy.http.Response) -> scrapy.Request:
        self.logger.info("Fanning out requests from %s", response.url)

        open_in_browser(response)

        for url in response.css("p > a[onclick]"):
            yield scrapy.FormRequest.from_response(response, formnumber=0, callback=self.dump)

    def dump(self, response: scrapy.http.Response):
        self.logger.info("Parsing %s", response.url)

        # Dump response
        with open("output.html", "ab") as f:
            f.write(response.body)


