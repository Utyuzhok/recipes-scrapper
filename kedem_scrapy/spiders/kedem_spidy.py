import scrapy
import re
from kedem_scrapy.items import DishItem


class DishesSpider(scrapy.Spider):
    name = "dishes"

    def start_requests(self):
        yield scrapy.Request(url='http://kedem.ru/recipe/', callback=self.section_urls)

    def section_urls(self, response):
        for section_href in response.css("div.w-row div.w-col-6 a.rmenu::attr(href)").extract():
            yield scrapy.Request(url='http://kedem.ru{}'.format(section_href), callback=self.page_urls)

    def page_urls(self, response):
        nav_text = response.css("div.navtext::text").extract_first()
        if nav_text is not None:
            max_page = re.findall(r"Стр. 1 из (\w+)", nav_text)
            for i in range(1, int(max_page[0])):
                yield scrapy.Request(url=response.url + str(i) + '/', callback=self.dish_urls)
        else:
            yield scrapy.Request(url=response.url, callback=self.dish_urls)


    def dish_urls(self, response):
        for dish_href in response.xpath("//a[@class='w-clearfix w-inline-block pgrblock']/@href").extract():
            yield scrapy.Request(url='http://kedem.ru{}'.format(dish_href), callback=self.dish_parser)

    def dish_parser(self, response):
        m = re.findall(r"http://kedem.ru/(\w+)/(\w+)/", response.url)
        href = '/' + m[0][0] + '/' + m[0][1] + '/'
        section = response.xpath("//a[@href='" + href + "'][@class='pathlink']/text()").extract_first()
        dish_name = response.css('h1.h1::text').extract_first()
        ings = [{'name': name} for name in response.xpath("//div[@itemprop='ingredients']/span/text()").extract() if name is not ' ']
        ings_quantity_list = response.xpath("//div[@itemprop='ingredients']/span/span[@style='float:right;min-width:50px;']/text()").extract()
        for i in range(len(ings_quantity_list)):
            ings[i]['quantity'] = ings_quantity_list[i]
        cooking_instructions = response.css('div.rtext p::text').extract()
        dish = DishItem()
        dish['section'] = section
        dish['name'] = dish_name
        dish['ings'] = ings
        dish['cooking_instructions'] = cooking_instructions
        yield dish