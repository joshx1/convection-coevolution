from bs4 import BeautifulSoup
import requests
import re
import sys
import numpy as np
from metpy.units import units
import metpy.calc as mpcalc
from tqdm import tqdm
import matplotlib.pyplot as plt

# Move forward 12 hours by 12 hours, if 12AM and 12 PM data both exists, take the average as the daily data. If next 24 hour block also exists, add the difference onto the overall coevolution calculation.

def get_csf_cape():
    a = 'lkdfhisoe78347834 (())&/&745  '
    months_short = [4,6,9,11]
    years_leap = [2004,2008,2012,2016,2020]
    for year in range(2000,2020):
        for month in range(1,13):
            cape_day_list = []
            cape_list = []
            csf_list = []
            time_list = []
            day_list = []
            month_list = []
            year_list = []
            if month == 2:
                if year in years_leap:
                    date_end = 29
                else:
                    date_end = 28
            elif month in months_short:
                date_end = 30
            else:
                date_end = 31
            for date in range(0,date_end):
                for time in range(0,2):
                    year = 2014
                    month = 8
                    date = 29
                    time = time* 12
                    time = str(time).zfill(2)
                    date = str(date).zfill(2)
                    # Jakarta
                    #url = "http://weather.uwyo.edu/cgi-bin/sounding?region=seasia&TYPE=TEXT%3ALIST&YEAR={}&MONTH={}&FROM={}{}&TO={}{}&STNM=96749".format(year,month,date,time,date,time)
                    # Guam
                    url = "http://weather.uwyo.edu/cgi-bin/sounding?region=se&TYPE=TEXT%3ALIST&YEAR={}&MONTH={}&FROM={}{}&TO={}{}&STNM=91212".format(year,month,date,time,date,time)
                    page = requests.get(url)
                    print(page)
                    print(page.status_code)
                    print('Month: {}'.format(month))
                    print('Year: {}'.format(year))
                    #while page.status_code != 200:
                    #    page = requests.get(url)
                    print(page)
                    print(page.status_code)
                    print('Month: {}'.format(month))
                    print('Year: {}'.format(year))
         
                    soup = BeautifulSoup(page.content, 'html.parser')

                    ## For the Date and Time ##
                    date = soup.find_all('h2')
                    #date = date[6].text
                    #print(date)
                    #wordlist = re.sub("[^\w]", " ",  date).split()
                    #print(wordlist[-4:])
                    #print(wordlist[-4:][0])

                    ## For the CAPE ##
                    midnight_data_exists = 0
                    noon_data_exists = 0
                    for i in tqdm(range(0,len(soup.find_all('pre')))):
                        p = soup.find_all('pre')[i]
                        if i % 2 == 1:
                            p = p.text.strip()
                            p = p.splitlines()
                            l1 = [k for k in p if 'Convective' in k and 'Potential' in k]
                            for i in range(0,len(l1)):
                                cape = float(re.sub("[^\d\.]",'', l1[i]))
                                cape_day_list.append(cape)
                                if int(time) == 12:
                                    noon_data_exists = 1
                                if int(time) == 0:
                                    midnight_data_exists = 1
                            #try:
                            #    cape
                            #except NameError:
                            #    print("CAPE UNDEFINED")
                        else:
                            date_current = date[int(i/2)].text
                            date_split = re.sub("[^\w]", " ",  date_current).split()[-4:]
                            time_list.append(date_split[0]) 
                            day_list.append(date_split[1]) 
                            month_list.append(date_split[2]) 
                            year_list.append(date_split[3]) 

                            p_array = np.array(p.text.strip().splitlines()[4].split())
                            p_array = p_array.astype(np.float)
                            p_list = []
                            for i in range(4,len(p.text.strip().splitlines())):
                                p_array = np.array(p.text.strip().splitlines()[i].split())
                                p_array = p_array.astype(np.float)
                                if len(p_array) == 11:
                                    p_list.append(p_array)
                            p_stack = np.stack(p_list)
                            p_stack = p_stack[p_stack[:,0] > 100]
                            pressure = p_stack[:,0]*100*units.pascal
                            temperature = p_stack[:,2]+273.15
                            temperature = temperature*units.kelvin
                            q = p_stack[:,5]/1000
                            pressure_diff = np.diff(pressure,axis = 0)

                            ## Calculate CSF ##
                            sat = mpcalc.saturation_mixing_ratio(pressure,temperature)
                            sat_weighted = sat.data[:-1] * pressure_diff
                            sat_sum = np.sum(sat_weighted)

                            q_weighted = q.data[:-1] * pressure_diff
                            q_sum = np.sum(q_weighted)

                            csf = (q_sum/sat_sum).magnitude
                            csf_list.append(csf)
                            #print(csf)
                if noon_data_exists == 1 and midnight_data_exists == 0:
                    cape_list.extend(cape_day_list)
                    csf_list.extend(csf_day_list)
                    time_list.extend(time_day_list)
                    month_list.extend(month_day_list)
                    year_list.extend(year_day_list)
            cape_list = np.array(cape_list)
            csf_list = np.array(csf_list)
            time_list = np.array(time_list)
            day_list = np.array(day_list)
            month_list = np.array(month_list)
            year_list = np.array(year_list)
            if np.shape(cape_list) != np.shape(csf_list):
                print('WARNING!!!!')
                print('Month: {}'.format(month))
                print('Year: {}'.format(year))
                sys.exit()
            print(np.nanmean(cape_list))
            print(np.nanmean(csf_list))
            print(time_list[1])
            print(day_list[1])
            print(month_list[1])
            print(year_list[1])
            print(np.shape(cape_list))
            print(np.shape(csf_list))
            print(np.shape(time_list))
            print(np.shape(day_list))
            print(np.shape(month_list))
            print(np.shape(year_list))
            np.save("jakarta/jakarta_cape_{}_{}".format(month,year),cape_list)
            np.save("jakarta/jakarta_csf_{}_{}".format(month,year),csf_list)
            np.save("jakarta/jakarta_time_{}_{}".format(month,year),time_list)
            np.save("jakarta/jakarta_day_{}_{}".format(month,year),day_list)
            np.save("jakarta/jakarta_month_{}_{}".format(month,year),month_list)
            np.save("jakarta/jakarta_year_{}_{}".format(month,year),year_list)
    return

def load_data():
    # loading data
    csf_all = []
    cape_all = []
    time_all = []
    day_all = []
    month_all = []
    year_all = []
    flag = 0
    for year in range(2010,2020):
        for month in range(1,13):
            if ((month == 8 and year == 2014) 
            or (month == 7 and year == 2013) 
            or (month == 3 and year == 2015) 
            or (month == 7 and year == 2015) 
            or (month == 8 and year == 2016) 
            or (month == 10 and year == 2016) 
            or (month == 2 and year == 2018) 
            or (month == 4 and year == 2018) 
            or (month == 7 and year == 2018) 
            or (month == 10 and year == 2018) 
            or (month == 3 and year == 2019)):
                flag = 1
            if flag == 0:
                csf = np.load("guam/guam_csf_{}_{}.npy".format(month,year))
                cape = np.load("guam/guam_cape_{}_{}.npy".format(month,year))
                time = np.load("guam/guam_time_{}_{}.npy".format(month,year))
                day = np.load("guam/guam_day_{}_{}.npy".format(month,year))
                month_data = np.load("guam/guam_month_{}_{}.npy".format(month,year))
                year_data = np.load("guam/guam_year_{}_{}.npy".format(month,year))

                csf_all = np.append(csf_all,csf)
                cape_all = np.append(cape_all,cape)
                time_all = np.append(time_all,time)
                day_all = np.append(day_all,day)
                month_all = np.append(month_all,month_data)
                year_all = np.append(year_all,year_data)
            flag = 0
    np.save("guam/guam_cape_all",cape_all)
    np.save("guam/guam_csf_all",csf_all)
    np.save("guam/guam_time_all",time_all)
    np.save("guam/guam_day_all",day_all)
    np.save("guam/guam_month_all",month_all)
    np.save("guam/guam_year_all",year_all)

    return 

def plot_attractor():
    csf = np.load("guam/guam_csf_all.npy")
    cape = np.load("guam/guam_cape_all.npy")
    day = np.load("guam/guam_day_all.npy")
    month = np.load("guam/guam_month_all.npy")
    #print(month)
    year = np.load("guam/guam_year_all.npy")
    time = np.load("guam/guam_time_all.npy")
    print(np.shape(csf))
    print(np.shape(cape))
    print(np.shape(day))
    print(np.shape(month))
    print(np.shape(year))
    print(np.shape(time))
    bins_csf= 14
    bin_fine = 15
    bins_precip=20
    precip_lower = 0
    precip_higher = 1
    csf_lower = -500
    csf_higher = 5000
    csf_binvalues = np.linspace(csf_lower+csf_higher/bins_csf,csf_higher-csf_higher/bins_csf,bins_csf)
    precip_binvalues = np.linspace(precip_lower+precip_higher/bins_precip,precip_higher-precip_higher/bins_precip,bins_precip)
    csf_binvalues_fine = np.linspace(csf_lower+csf_higher/bins_csf,csf_higher-csf_higher/bins_csf,bin_fine)
    precip_binvalues_fine = np.linspace(precip_lower+precip_higher/bins_precip,precip_higher-precip_higher/bins_precip,bin_fine)
    counts1=np.zeros(shape=(bins_csf+1,bins_precip+1))
    counts2=np.zeros(shape=(bins_csf+1,bins_precip+1))
    counts3=np.zeros(shape=(bins_csf+1,bins_precip+1))

    counts2_fine=np.zeros(shape=(bin_fine+1,bin_fine+1))
    arrow_dirs = np.zeros(shape=(bins_csf+1,bins_precip+1,2))
    arrows = np.zeros(shape=(bins_csf+1,bins_precip+1,2))
    arrow_dirs = np.zeros(shape=(bins_csf+1,bins_precip+1,2))
    bin_loc2=np.zeros(shape=(2),dtype=int)

    bin_loc2_fine=np.zeros(shape=(2),dtype=int)
    flag = 0 
    temp = 0
    for i in range (2,len(time)-5):
        if time[i-2] == time[i] and time[i] == time[i+2]:
            if day_conditions(int(day[i-2]),int(day[i]),int(day[i+1]),month[i],year[i]) == 1:
                flag = 1
        if flag == 1:
            temp = temp+1
            csf1 = csf[i-2]
            csf2 = csf[i]
            csf3 = csf[i+2]
            
            cape1 = cape[i-2]
            cape2 = cape[i]
            cape3 = cape[i+2]
            precip1 = csf1
            precip2 = csf2
            precip3 = csf3
            csf1 = cape1
            csf2 = cape2
            csf3 = cape3
            arrow_precip = precip3 - precip1
            arrow_csf = csf3 - csf1
            bin_loc2[0]=int(np.digitize(csf2,csf_binvalues))
            bin_loc2[1]=int(np.digitize(precip2,precip_binvalues))
            arrow_dirs[bin_loc2[0],bin_loc2[1],0]=arrow_csf+arrow_dirs[bin_loc2[0],bin_loc2[1],0]
            arrow_dirs[bin_loc2[0],bin_loc2[1],1]=arrow_precip+arrow_dirs[bin_loc2[0],bin_loc2[1],1]
            counts2[bin_loc2[0],bin_loc2[1]]=counts2[bin_loc2[0],bin_loc2[1]]+1
       
            bin_loc2_fine[0]=int(np.digitize(csf2,csf_binvalues_fine))
            bin_loc2_fine[1]=int(np.digitize(precip2,precip_binvalues_fine))

            counts2_fine[bin_loc2_fine[0],bin_loc2_fine[1]]=counts2_fine[bin_loc2_fine[0],bin_loc2_fine[1]]+1
            flag = 0

    arrow_dirs[:,:,0]=np.divide(arrow_dirs[:,:,0],counts2[:,:])
    arrow_dirs[:,:,1]=np.divide(arrow_dirs[:,:,1],counts2[:,:])
    for i in range(0,bins_csf+1):
        for j in range(0,bins_precip+1):
            if counts2[i,j]<5:
                arrow_dirs[i,j,:]=0

    for i in range(0,bin_fine+1):
        for j in range(0,bin_fine+1):
            if counts2_fine[i,j]<5:
                counts2_fine[i,j] = float("nan")
    print(temp)
    np.savetxt("csf_arrows.csv", arrow_dirs[:,:,0], delimiter=",")
    np.savetxt("precip_arrows.csv", arrow_dirs[:,:,1], delimiter=",")
    np.savetxt("counts2.csv", counts2_fine, delimiter=",")
    counts2_fine = np.log10(np.divide(counts2_fine,np.nansum(counts2_fine)))

    # Define colormap # 

    X,Y=np.meshgrid(np.linspace(csf_lower,csf_higher,bins_csf+1),np.linspace(0,precip_higher,bins_precip+1))
    X_fine,Y_fine=np.meshgrid(np.linspace(csf_lower,csf_higher,bin_fine+1),np.linspace(0,precip_higher,bin_fine+1))
    plt.contourf(X_fine,Y_fine,np.transpose(counts2_fine),30)
    
    plt.quiver(X,Y,np.transpose(arrow_dirs[:,:,0]),np.transpose(arrow_dirs[:,:,1]), angles='xy', scale_units='xy', scale=1, pivot='mid')
    plt.colorbar(label = 'Log10(Percent of total observations)',orientation='vertical')
    plt.xlabel('CAPE [J/kg]')
    plt.ylabel('CSF')
    #plt.show()
    plt.title('Guam, Co-evolution of CAPE-CSF over 48 hours')
    plt.savefig('test',dpi=300)
    plt.close()
    return

def day_conditions(day0,day1,day2,month,year):

    months_short_Aug = ['Apr','Jun','Aug','Sep','Nov']
    if day0 == day1-1 and day2 == day1+1:
        return True
    elif month in months_short_Aug and day0 == 31 and day2 == day1+1:
        return True

    elif month in months_short_Aug and day0 == 29 and day2 == 1:
        return True
    elif day0 == 30 and day2 == 1:
        return True

    elif month == 3 and day0 == 28 and day2 == day1+1:
        return True
    else:
        return False
#    elif month == 2 and day0 == 

def main():
    get_csf_cape()
    #load_data()
    #plot_attractor()

if __name__ == "__main__":
    main()
