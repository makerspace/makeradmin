import urllib3
from bs4 import BeautifulSoup
import time
import json

urls = [
    "/product/medlemsavgift",
    "/product/labbmedlemskap-1-m%C3%A5nad",
    "/product/labbavgift-3-m%C3%A5nader",
    "/product/labbavgift-halv%C3%A5r",
    "/product/labbavgift-hel%C3%A5r",
    "/product/startpaket",
    "/product/donation",
    "/product/tygkasse",
    "/product/g%C3%A5vokort-4723415",
    "/product/akrylplast",
    "/product/driftskostnad-laserskarare",
    "/product/bjorkplywood",
    "/product/mdf",
    "/product/st%C3%A4mpelgummi",
    "/product/textiltransfer-100mm-5160793",
    "/product/textiltransfer-100mm",
    "/product/sj%C3%A4lvh%C3%A4ftande-vinyl",
    "/product/st%C3%A5l-100g",
    "/product/aluminium",
    "/product/plast-100g",
    "/product/m%C3%A4ssing",
    "/product/akrylplast-20mm",
    "/product/v%C3%A4ndsk%C3%A4r-dcgt-0702-steel",
    "/product/v%C3%A4ndsk%C3%A4r-dcmt-0702-alu",
    "/product/v%C3%A4ndsk%C3%A4r-wnmg-0604-steel",
    "/product/v%C3%A4ndsk%C3%A4r-wnmg-0604-alu",
    "/product/v%C3%A4ndsk%C3%A4r-rcmt-0803-steel",
    "/product/v%C3%A4ndsk%C3%A4r-rcgt-0803-alu",
    "/product/v%C3%A4ndsk%C3%A4r-mgmn-200-steel",
    "/product/v%C3%A4ndsk%C3%A4r-mggn-20-alu",
    "/product/v%C3%A4ndsk%C3%A4r-er-16-ag60-steel",
    "/product/v%C3%A4ndsk%C3%A4r-er-16-ag60-alu",
    "/product/v%C3%A4ndsk%C3%A4r-ir-16-ag60-steel",
    "/product/v%C3%A4ndsk%C3%A4r-ir-16-ag60-alu",
    "/product/sparskar",
    "/product/pinnfr%C3%A4s-f%C3%B6r-plast-7892191",
    "/product/pinnfr%C3%A4s-f%C3%B6r-aluminium",
    "/product/fullradiefr%C3%A4s-f%C3%B6r-aluminium",
    "/product/gravyrfr%C3%A4s-30-grader-01mm",
    "/product/pinnfr%C3%A4s-f%C3%B6r-st%C3%A5l",
    "/product/labbmedlemskap-1-m%C3%A5nad",
    "/product/labbavgift-3-m%C3%A5nader",
    "/product/labbavgift-halv%C3%A5r",
    "/product/labbavgift-hel%C3%A5r",
    "/product/startpaket",
    "/product/g%C3%A5vokort-4723415",
    "/product/donation",
    "/product/tygkasse",
    "/product/v%C3%A4ndsk%C3%A4r-dcgt-0702-steel",
    "/product/v%C3%A4ndsk%C3%A4r-dcmt-0702-alu",
    "/product/v%C3%A4ndsk%C3%A4r-wnmg-0604-steel",
    "/product/v%C3%A4ndsk%C3%A4r-wnmg-0604-alu",
    "/product/v%C3%A4ndsk%C3%A4r-rcmt-0803-steel",
    "/product/v%C3%A4ndsk%C3%A4r-rcgt-0803-alu",
    "/product/v%C3%A4ndsk%C3%A4r-mgmn-200-steel",
    "/product/v%C3%A4ndsk%C3%A4r-mggn-20-alu",
    "/product/v%C3%A4ndsk%C3%A4r-er-16-ag60-steel",
    "/product/v%C3%A4ndsk%C3%A4r-er-16-ag60-alu",
    "/product/v%C3%A4ndsk%C3%A4r-ir-16-ag60-steel",
    "/product/v%C3%A4ndsk%C3%A4r-ir-16-ag60-alu",
    "/product/sparskar",
    "/product/pinnfr%C3%A4s-f%C3%B6r-plast-7892191",
    "/product/pinnfr%C3%A4s-f%C3%B6r-aluminium",
    "/product/fullradiefr%C3%A4s-f%C3%B6r-aluminium",
    "/product/gravyrfr%C3%A4s-30-grader-01mm",
    "/product/pinnfr%C3%A4s-f%C3%B6r-st%C3%A5l",
    "/product/akrylplast",
    "/product/driftskostnad-laserskarare",
    "/product/bjorkplywood",
    "/product/mdf",
    "/product/st%C3%A4mpelgummi",
    "/product/textiltransfer-100mm-5160793",
    "/product/textiltransfer-100mm",
    "/product/sj%C3%A4lvh%C3%A4ftande-vinyl",
    "/product/st%C3%A5l-100g",
    "/product/aluminium",
    "/product/plast-100g",
    "/product/m%C3%A4ssing",
    "/product/akrylplast-20mm",
]

http = urllib3.PoolManager()

result = []

for url in urls:
    soup = BeautifulSoup(http.request('GET', 'http://makerspace.tictail.com' + url).data, "lxml")
    description = "".join([str(x) for x in soup.find(class_="description").contents])
    price = soup.find(class_="price_tag").text
    assert(price.endswith(" SEK"))
    price = price[:-4]
    title = soup.find("h1").text
    variations = soup.find(class_="tictail_variations_select")
    image = soup.find(class_="fullscreen_image")

    if image is not None:
        image = image["href"]
        image = image.split(".jpeg")[0] + ".jpeg"

    if variations is not None:
        for option in variations.children:
            price = float(option["data-original-price"])
            inner = option.text
            ending = " ({0:g} SEK)".format(price)
            assert inner.endswith(ending), inner + " does not end with " + ending
            inner = inner[:-len(ending)]

            result.append({
                "name": title,
                "suffix": inner,
                "image": image,
                "price": price,
                "description": description
            })
    else:
        result.append({
            "name": title,
            "suffix": "",
            "image": image,
            "price": price,
            "description": description
        })

with open("tictail.json", "w") as f:
    f.write(json.dumps(result))
