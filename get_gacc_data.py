# imports
import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_fullBulletin_data_years():
    """Scrapes the GACC Website's full bulletin section to return a list of years for which they have data. Returns years as a list is descending order, from current year to lowest."""
    
    # note for when being called by other function
    print('Getting list of possible years from GACC...')
    
    # setup base url for full monthly bulletin webpage
    fullb_url = 'http://english.customs.gov.cn/statics/report/monthly.html'
    
    # make a get request
    fullb_response = requests.get(fullb_url)
    # use Beautiful Soup to parse and create soup
    fullb_soup = BeautifulSoup(fullb_response.text, 'html.parser')
    
    # find the list of years offered
    select_years = fullb_soup.find('select', id='monthlysel')
    # create and empty list
    # append the values in our stripped strings to the list 
    list_years = []
    for value in select_years.stripped_strings:
        list_years.append(value)
    
    return list_years

def get_global_monthly_links(some_list):
    """Scrapes the GACC Website for the list of given years. Collects the links for the latest_monthly bulletin in each year and returns a dictionary with years as keys and values as the latest link within that year."""
    
    # note for when being called by other function
    print('Getting latest / final monthly bulletin links for each possible year...')
    
    # setup empty dict to collect links
    dict_year_link = {}
    
    # setup the url for request to be made to depending on list position
    for index, year in enumerate(some_list):
        
        # add the year onto the url unless looking at latest year
        # gacc makes current year plain, with no added digits
        url_add = year if index>0 else ''         
        
        # set the url for full monthly bulletin webpage based upon our add in
        fullb_url = f'http://english.customs.gov.cn/statics/report/monthly{url_add}.html'
        # make a get request
        fullb_response = requests.get(fullb_url)
        # use Beautiful Soup to parse and create soup
        fullb_soup = BeautifulSoup(fullb_response.text, 'html.parser')

        # finding the links for each monthly totals summary
        monthly_total_links = fullb_soup.find_all('td')[3].find_all('a')

        # latest / last link in year
        latest_month_link = monthly_total_links[-1]['href']
        
        # put into dictionary, key is year and value is the link
        dict_year_link[year] = latest_month_link
        
    
    # return the dictionary once loop is finished
    return dict_year_link
        

def get_global_dataframes(list_years, dict_of_links):
    """Takes a list of years and dictionary of years/links, and fetches dates, 
    imports and exports from a GACC monthly bulletin page. 
    Collects from all the relevant years and converts each to a dataframe and 
    returns these dataframes in a list"""
    
    # note for when being called by other function
    print('Getting data for each individual link / bulletin')
    
    list_of_dfs =[]
    
    # make sure it is sorted into ascending order
    # need this to ensure dfs come in ascending order
    list_years.sort()
    
    # for each of our years
    for year in list_years:
        
        # grab the url from our dictonary
        month_url = dict_of_links[year]
        
        # make a get request to this first url
        month_html_doc = requests.get(month_url)
        # parse the html with beautiful soup
        month_soup = BeautifulSoup(month_html_doc.content, 'html.parser')
        
        # finding a table object from our soup object
        table_object = month_soup.find('div', attrs={'class':'atcl-cnt'}).find('table')
        
        # defining an empty pandas dataframe to collect out data
        # give it column names only
        df = pd.DataFrame(columns=['date', 'export', 'import'])

        # delving into our table object

        # find all the rows in our table object
        for row in table_object.tbody.find_all('tr'):
            # find all data for each column in that row
            columns = row.find_all('td')

            # Now definte under which conditions we will add data to our dataframe

            # 1. Check it is not an empty list
            if columns != []:
                # 2. Check the length of the row (no columns) is greater than 4
                if len(columns) > 4:
                    # 3. Check it's not the table header row
                    if (columns[0].text.strip() != 'Year&Month'):
                        # 4. And that date column isn't empty
                        if (columns[0].text.strip() != ''):

                            # under these conditions, extract columns for date, exports & imports

                            # remove commas so can convert to numeric
                            # change dot for hyphen in date for pd.datetime conversion
                            Date = columns[0].text.strip().replace('.','-')
                            Export = columns[2].text.strip().replace(',','')
                            Import = columns[3].text.strip().replace(',','')

                            # append these new values to our empty dataframe
                            df = df.append({'date':Date, 'export':Export, 'import':Import},
                                            ignore_index=True)

        # perform some light pre-processing of our dataframe                    

        # convert export and import columns to numeric
        for col in df.columns[1:]:  # skip col 0, which is date
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # convert the date column to datetime and set as index
        df['date'] = pd.to_datetime(df.date)

        # set the date as the index, perform in place
        # leave the dropping of old date col as true
        df.set_index('date', drop=True, inplace=True)
        
        list_of_dfs.append(df)
        
    return list_of_dfs

def create_single_global_df(list_of_dfs):
    """Takes a list of ascending order dfs but with duplicated values. Appends them all together and keeps only the last of each duplicate (which is a better / more revised version). Returns one large dataframe."""
    
    # note for when being called by other function
    print('Converting links to one giant dataframe')
    
    for i in range(len(list_of_dfs)):
        if i == 0:
            new_df=list_of_dfs[i]
        else:
            new_df = new_df.append(list_of_dfs[i])

    # reset the index so date becomes a column
    new_df=new_df.reset_index()

    # drop the duplicates, and keep the last one in each case 
    # this gives us the most recently revised data in each case
    new_df = new_df.drop_duplicates(subset=['date'], keep='last')

    # set the date column as index again
    new_df.set_index('date', inplace=True)

    # return the large combined df
    return new_df


def get_monthly_global_trade():
    """Scrape GACC website to get data on China's monthly goods imports and exports, 
        from oldest published on website through to most current. 
        Returns a dataframe of two time-series in ascending order with datetime index."""
    
    # get our list of years
    list_years = get_fullBulletin_data_years()
    
    # get the final / latest bulletin for each year
    dict_years_links = get_global_monthly_links(list_years)
    
    # get a list of individual dataframes
    list_dfs = get_global_dataframes(list_years, dict_years_links)
    
    # create one large df from all the lists.
    df = create_single_global_df(list_dfs)
    
    # return our nice finished data
    return df
    

def get_monthly_partner_links(years_list):
    """Takes list of years available for GACC monthly bulletins. 
    Finds a list of monthly trade-by-partner links for each.
    Returns a long list of trade by partner links for all years"""
    
    # create an empty dictionary for collecting out links
    dict_months_partner_links = {}
    
    # setup the url for request to be made to depending on list position
    for index, year in enumerate(years_list):
        
        # add the year onto the url unless looking at latest year
        # gacc makes current year plain, with no added digits
        url_add = year if index>0 else ''         

        # set the url for full monthly bulletin webpage based upon our add in
        fullb_url = f'http://english.customs.gov.cn/statics/report/monthly{url_add}.html'

        # make a get request
        fullb_response = requests.get(fullb_url)
        # use Beautiful Soup to parse and create soup
        fullb_soup = BeautifulSoup(fullb_response.text, 'html.parser')
        
        # setup a months dictionary for getting numeric onths
        months_dict={'Jan.':'01', 'Feb.':'02','Mar.':'03','Apr.':'04',
                     'May.':'05','Jun.':'06','Jul.':'07','Aug.':'08',
                     'Sep.':'09','Oct.':'10','Nov.':'11','Dec.':'12'}

        # find the links to trade by partner country
        by_partner_links = fullb_soup.find_all('td')[5].find_all('a')
        
        # look through the partner links, with i-indexing
        for i in range(len(by_partner_links)):
            
            # creating the key for dictionary
            # get the month listing from html, convert to numeric with our dict
            # create a date-string with year and month
            temp_month = by_partner_links[i].text.strip()
            temp_month = months_dict[temp_month]
            temp_key = f"{year}-{temp_month}"
            
            # add the relevant link into our dictionary
            # use the newly created temp key (which is a date-string)
            dict_months_partner_links[temp_key] = by_partner_links[i]['href']
        
    # return the dictionary 
    return dict_months_partner_links


def get_monthly_partner_dfs(dict_of_links):
    """Uses our dictionary of links to make get requests to individual monthly pages for trade by partner country. Extracts the table data and returns a dictionary with monthly dataframes as values and and months as the keys."""
    
    # create an empty dict to collect dataframes
    dict_months_partner_dfs = {}
    
    # sort and loop through our dictionary
    for key in sorted(dict_of_links):
        # get the relevant link from our dictionary
        link = dict_of_links[key]
        
        # print out a message to announce where am in process
        print(f"Collecting data for {key}")
        
        # set the url equal to our link
        partner_url = link
        # use requests to retreive the response
        partner_response = requests.get(partner_url)
        # use BeautifulSoup to parse and create soup
        partner_soup = BeautifulSoup(partner_response.text, 'html.parser')
        
        # find the partner table object
        partner_table = partner_soup.find('div', attrs={'class':'atcl-layout'}).find('table')
        
        # create an empty dataframe
        df = pd.DataFrame(columns=['partner', 'export', 'import'])

        # find all the rows in our table object
        for row in partner_table.tbody.find_all('tr'):
            # find all data for each column in that row
            columns = row.find_all('td')

            # set some conditions for adding into our df
            if columns != []:                          # not an empty list
                if len(columns) > 6:                   # if more than 6 columns
                    if columns[0].text.strip() != '':  # removes empty rows
                        if columns[0].text.strip().isnumeric() == False: # removes time label rows

                            # extract the partner name, exports and imports columns
                            # use relevant index of our columns object
                            # then take text part and strip. 
                            # for exports and imports, remove commas and replace any hyphens with zero
                            Partner = columns[0].text.strip()
                            Exports = columns[3].text.strip().replace(',','').replace('-','0')
                            Imports = columns[5].text.strip().replace(',','').replace('-','0')

                            # append these new values to our empty dataframe
                            df = df.append({'partner':Partner, 'export':Exports, 'import':Imports},
                                            ignore_index=True)
        
        # add a date column to our df based on our key
        df['date'] = key
        
        # add our dataframe into our collector
        dict_months_partner_dfs[key] = df
        
    # return our dictionery object
    return dict_months_partner_dfs

def add_region_partner_df(df):
    """Takes a trade dataframe (partner, export, import, date) and adds a region to it based on our custom rules. Also cleans up the partner names. Returns the edited dataframe."""
    
    # create an empty list for collecting regions
    region_list = []   
    # loop through list of partners
    # append a region based on different cases
    # use a carry term
    for term in df.partner:
        if term == term.upper():             # if all caps
            region_list.append('Region') 
        elif term[-1] == ':':                  # if ends with a colon
            region_list.append('Region')
            carry_region = term[:-1]         # make this a carry term for rows below
        elif term == 'Countries(reg.)unknown': # handle unknowns
            region_list.append('Unknown')
        else:                                # for normal cases
            region_list.append(carry_region)
    
    # add the regions to the df
    df['region'] = region_list
    
    # fix partner names
    # empty list for collecting
    partner_list = []
    # change total to world
    # remove ':' and other weird text
    for partner in df.partner:
        if partner == 'TOTAL':
            partner_list.append('World')
        else:
            partner_list.append(partner.replace(':','').replace('ï¼\x8cChina',''))
    
    # add edited lists back to df
    df['partner'] = partner_list
    
    # return our edited df
    return df
    

        
