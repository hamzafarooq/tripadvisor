#!/usr/bin/env python
from datetime import datetime
from time import time
from lxml import html,etree
from review_v2 import scrape, write_in_csv
import pandas as pd
import requests,re
import os,sys
import unicodecsv as csv
import argparse

def parse(locality,checkin_date,checkout_date,sort):
    checkIn = checkin_date.strftime("%Y/%m/%d")
    checkOut = checkout_date.strftime("%Y/%m/%d")
    print ("Scraper Inititated for Locality:%s"%locality)
    # TA rendering the autocomplete list using this API
    print ("Finding search result page URL")
    header = {

                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
            }
    geo_url = 'https://www.tripadvisor.com/TypeAheadJson?action=API&startTime='+str(int(time()))+'&uiOrigin=GEOSCOPE&source=GEOSCOPE&interleaved=true&types=geo,theme_park&neighborhood_geos=true&link_type=hotel&details=true&max=12&injectNeighborhoods=true&query='+locality
    api_response  = requests.get(geo_url,headers=header, timeout=120).json()
    #getting the TA url for th equery from the autocomplete response

    #add multiple urls below to get a larger list of HOTELS see url:
    #https://www.tripadvisor.com/Hotels-g45963-Las_Vegas_Nevada-Hotels.html
    #https://www.tripadvisor.com/Hotels-g45963-oa30-Las_Vegas_Nevada-Hotels.html - ths is page 2

    url_from_autocomplete = "http://www.tripadvisor.com"+api_response['results'][0]['url']
    print ('URL found %s'%url_from_autocomplete)
    geo = api_response['results'][0]['value']
    a=url_from_autocomplete
    b=a.split("-")
    s="-"
    c=s.join([b[0],b[1],"oa30",b[2],b[3]])
    d=s.join([b[0],b[1],"oa60",b[2],b[3]])
    urllist = [a,c,d]
    #Formating date for writing to file

    date = checkin_date.strftime("%Y_%m_%d")+"_"+checkout_date.strftime("%Y_%m_%d")
    #form data to get the hotels list from TA for the selected date
    form_data = {'changeSet': 'TRAVEL_INFO',
            'showSnippets': 'false',
            'staydates':date,
            'uguests': '2',
            'sortOrder':sort
    }

    all_hotel=[]
    for url_from_autocomplete in urllist:
        print(url_from_autocomplete)

        headers = {
                                'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
                                'Accept-Encoding': 'gzip,deflate',
                                'Accept-Language': 'en-US,en;q=0.5',
                                'Cache-Control': 'no-cache',
                                'Connection': 'keep-alive',
                                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                                'Host': 'www.tripadvisor.com',
                                'Pragma': 'no-cache',
                                'Referer': url_from_autocomplete,     
                                 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:28.0) Gecko/20100101 Firefox/28.0',
                            }
        cookies=  {"SetCurrency":"USD"}
        print ("Downloading search results page")
        page_response  = requests.post(url = url_from_autocomplete,data=form_data,headers = headers, cookies = cookies, timeout=120)
        print ("Parsing results ")
        parser = html.fromstring(page_response.text)
        hotel_lists = parser.xpath('//div[contains(@class,"listItem")]//div[contains(@class,"listing collapsed")]')
        hotel_data = []
        if not hotel_lists:
            hotel_lists = parser.xpath('//div[contains(@class,"listItem")]//div[@class="listing "]')

        for hotel in hotel_lists:
            XPATH_HOTEL_LINK = './/a[contains(@class,"property_title")]/@href'
            XPATH_REVIEWS  = './/a[@class="review_count"]//text()'
            XPATH_RANK = './/div[@class="popRanking"]//text()'
            XPATH_RATING = './/span[contains(@class,"rating")]/@alt' #update this code to get rating
            XPATH_HOTEL_NAME = './/a[contains(@class,"property_title")]//text()'
            XPATH_HOTEL_FEATURES = './/div[contains(@casls,"common_hotel_icons_list")]//li//text()'
            XPATH_HOTEL_PRICE = './/div[contains(@data-sizegroup,"mini-meta-price")]/text()'
            XPATH_VIEW_DEALS = './/div[contains(@data-ajax-preserve,"viewDeals")]//text()'
            XPATH_BOOKING_PROVIDER = './/div[contains(@data-sizegroup,"mini-meta-provider")]//text()'

            raw_booking_provider = hotel.xpath(XPATH_BOOKING_PROVIDER)
            raw_no_of_deals =  hotel.xpath(XPATH_VIEW_DEALS)
            raw_hotel_link = hotel.xpath(XPATH_HOTEL_LINK)
            raw_no_of_reviews = hotel.xpath(XPATH_REVIEWS)
            raw_rank = hotel.xpath(XPATH_RANK)
            raw_rating = hotel.xpath(XPATH_RATING)
            raw_hotel_name = hotel.xpath(XPATH_HOTEL_NAME)
            raw_hotel_features = hotel.xpath(XPATH_HOTEL_FEATURES)
            raw_hotel_price_per_night  = hotel.xpath(XPATH_HOTEL_PRICE)

            url = 'https://www.tripadvisor.com'+raw_hotel_link[0] if raw_hotel_link else  None
            reviews = ''.join(raw_no_of_reviews).replace("reviews","").replace(",","") if raw_no_of_reviews else 0
            rank = ''.join(raw_rank) if raw_rank else None
            rating = ''.join(raw_rating).replace('of 5 bubbles','').strip() if raw_rating else None
            name = ''.join(raw_hotel_name).strip() if raw_hotel_name else None
            hotel_features = ','.join(raw_hotel_features)
            #price_per_night = ''.join(raw_hotel_price_per_night).encode('utf-8').replace('\n','') if raw_hotel_price_per_night else None
            price_per_night = ''.join(raw_hotel_price_per_night).replace('\n','') if raw_hotel_price_per_night else None

            no_of_deals = re.findall("all\s+?(\d+)\s+?",''.join(raw_no_of_deals))
            booking_provider = ''.join(raw_booking_provider).strip() if raw_booking_provider else None

            if no_of_deals:
                no_of_deals = no_of_deals[0]
            else:
                no_of_deals = 0

            data = {
                        'hotel_name':name,
                        'url':url,
                        'locality':locality,
                        'reviews':reviews,
                        'tripadvisor_rating':rating,
                        'checkOut':checkOut,
                        'checkIn':checkIn,
                        'hotel_features':hotel_features,
                        'price_per_night':price_per_night,
                        'no_of_deals':no_of_deals,
                        'booking_provider':booking_provider

            }
            hotel_data.append(data)
            all_hotel.append(data)
    #Referrer is necessary to get the correct response from TA if not provided they will redirect to home page
    #print(all_hotel)
    return all_hotel

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('checkin_date',help = 'Hotel Check In Date (Format: YYYY/MM/DD')
    parser.add_argument('checkout_date',help = 'Hotel Chek Out Date (Format: YYYY/MM/DD)')
    sortorder_help = """
    available sort orders are :\n
    priceLow - hotels with lowest price,
    distLow : Hotels located near to the search center,
    recommended: highest rated hotels based on traveler reviews,
    popularity :Most popular hotels as chosen by Tipadvisor users
    """
    parser.add_argument('sort',help = sortorder_help,default ='popularity ')
    parser.add_argument('locality',help = 'Search Locality')
    args = parser.parse_args()
    locality = args.locality
    checkin_date = datetime.strptime(args.checkin_date,"%Y/%m/%d")
    checkout_date = datetime.strptime(args.checkout_date,"%Y/%m/%d")
    sort= args.sort
    checkIn = checkin_date.strftime("%Y/%m/%d")
    checkOut = checkout_date.strftime("%Y/%m/%d")
    today = datetime.now()

    if today<datetime.strptime(checkIn,"%Y/%m/%d") and datetime.strptime(checkIn,"%Y/%m/%d")<datetime.strptime(checkOut,"%Y/%m/%d"):
        data = parse(locality,checkin_date,checkout_date,sort)
        print ("Writing to output file tripadvisor_data.csv")
        with open('tripadvisor_data.csv','wb')as csvfile:
            fieldnames = ['hotel_name','url','locality','reviews','tripadvisor_rating','checkIn','checkOut','price_per_night','booking_provider','no_of_deals','hotel_features']
            my_df  = pd.DataFrame(columns = fieldnames)
            for row in  data:
                my_df.loc[len(my_df)] = [row['hotel_name'],row['url'],row['locality'],row['reviews'],row['tripadvisor_rating'],row['checkIn'],row['checkOut'],row['price_per_night'],row['booking_provider'],row['no_of_deals'],row['hotel_features']]
            DB_COLUMN   = 'review_body'
            DB_COLUMN1 = 'review_date'
            DB_COLUMN2 = 'hotelName' #this needs to be cleaned for cleaner titles
            DB_COLUMN3 = 'hotelUrl'
            start_urls = []
            for index, row2 in my_df.iterrows():
                start_urls.append(row2['url'])
            lang = 'en'

            headers = [
            DB_COLUMN,
            DB_COLUMN1,
            DB_COLUMN2,
            DB_COLUMN3
            ]
            reviews_df  = pd.DataFrame(columns = headers)
            for url in start_urls:

                # get all reviews for 'url' and 'lang'
                items = scrape(url, lang)
                filename = 'hotelReviewsIn' + locality + '__' + lang
                filename2 = "HotelListIn" + locality + '__' + lang
                if not items:
                    print('No reviews')
                else:
                    # write in CSV
                    for i in items:
                        reviews_df.loc[len(reviews_df)] = [i['review_body'],i['review_date'],my_df.loc[my_df['url'] == url]['hotel_name'], url]
            ci = checkIn.replace("/", "")
            co = checkOut.replace("/", "")
            reviews_df.to_csv(filename + ci +co+'.csv', encoding='utf-8')
            my_df.to_csv(filename2 + ci +co+'.csv', encoding='utf-8')
    #checking whether the entered date is already passed
    elif today>datetime.strptime(checkIn,"%Y/%m/%d") or today>datetime.strptime(checkOut,"%Y/%m/%d"):
        print ("Invalid Checkin date: Please enter a valid checkin and checkout dates,entered date is already passed")

    elif datetime.strptime(checkIn,"%Y/%m/%d")>datetime.strptime(checkOut,"%Y/%m/%d"):
        print ("Invalid Checkin date: CheckIn date must be less than checkOut date")
