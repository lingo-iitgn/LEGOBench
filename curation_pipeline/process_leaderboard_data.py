import pandas as pd
import pickle
from tqdm.notebook import tqdm
import json
import pickle5 as p5
import pandas as pd
import requests
import re
import bs4
from bs4 import BeautifulSoup
from collections import defaultdict
import time


def convert_str_to_expr(t):
    if type(t) == bs4.element.Script:
        t = str(t)
    if type(t) == str:
        t = t.replace("null", "None")
        t = t.replace("false", "False")
        t = t.replace("true", "True")
        t = t.replace("NaN", "None")
        return eval(t)
    elif type(t) == list:
        if type(t[0]) == str:
            t = t.replace("null", "None")
            t = t.replace("false", "False")
            t = t.replace("true", "True")
            t = t.replace("NaN", "None")
            return [eval(t)]
    else:
        print(f"CHECK STRING RETRIEVED: {type(t)} {t}")
        return t
    
def fetch_page_details(purl):
    response = requests.get(purl)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Find the <script> elements by ID
    evaluation_table_data = soup.find("script", id="evaluation-table-data")
    dataset_details = soup.find("script", id="dataset-details")
    #print("DD: ", dataset_details.contents)
    sota_page_details = soup.find("script", id="sota-page-details")
    evaluation_table_metrics_details = soup.find("script", id="evaluation-table-metrics")

    data_dict = {'dataset_details': dataset_details.string if dataset_details else None, 'sota_page_details': sota_page_details.string if sota_page_details else None, 'evaluation_table_data': evaluation_table_data.string if evaluation_table_data else None, 'evaluation_table_metrics': evaluation_table_metrics_details.string if evaluation_table_metrics_details else None}
    
    return data_dict

def get_arxivid_from_pwc(purl):
    if not purl:
        return None
    base_url = "https://paperswithcode.com" + purl
    response = requests.get(base_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        spans = soup.find_all('a', {'class': 'badge badge-light'}, href=True)
        if spans:
            for span in spans:
                pwcurl = span['href']
                if pwcurl.find('arxiv.org') > -1:
                    try:
                        arxiv_url = span['href']
                        arxid = arxiv_url.rsplit("/", 1)[-1]
                        versionmatch = re.search('v[0-9][0-9]*.pdf', arxid)
                        if versionmatch:
                            arxid = arxid[0:versionmatch.start()]
                        return arxid
                    except Exception as ex:
                        print(f"arxivid error: {purl}")
                        print(ex)
                else:
                    continue
        else:
            print(f"arxivid span not found: {purl}")
    return None


with open('../dataset/PwC_Source_Code.pkl', 'rb') as f:
    pwc_html = p5.load(f)

pwcpageurl_arxiv_map = {}
intermediate_pwc_leaderboards = defaultdict(dict)
not_found_metrics = []

for d in pwc_html:
    print(d)
    start_time = time.time()
    for t in pwc_html[d]:
        metric_dir_dict = {}
        try:
            try:
                print(t)
                requested_once = False
                if not convert_str_to_expr(pwc_html[d][t]['dataset_details_content']):
                    #print("Retrieving page source")
                    all_data_dict = fetch_page_details(t)
                    requested_once = True
                    pwc_html[d][t]['dataset_details_content'] = all_data_dict['dataset_details']
                    if not convert_str_to_expr(pwc_html[d][t]['sota_page_details_content']):
                        pwc_html[d][t]['sota_page_details_content'] = all_data_dict['sota_page_details']
                    if not convert_str_to_expr(pwc_html[d][t]['evaluation_table_data_content']):
                        pwc_html[d][t]['evaluation_table_data_content'] = all_data_dict['evaluation_table_data']
                    if not convert_str_to_expr(pwc_html[d][t]['evaluation_table_metrics_content']):
                        pwc_html[d][t]['evaluation_table_metrics_content'] = all_data_dict['evaluation_table_metrics']

                if not convert_str_to_expr(pwc_html[d][t]['sota_page_details_content'])  and not requested_once:
                    all_data_dict = fetch_page_details(t)
                    requested_once = True
                    pwc_html[d][t]['sota_page_details_content'] = all_data_dict['sota_page_details']
                    if not convert_str_to_expr(pwc_html[d][t]['evaluation_table_data_content']):
                        pwc_html[d][t]['evaluation_table_data_content'] = all_data_dict['evaluation_table_data']
                    if not convert_str_to_expr(pwc_html[d][t]['evaluation_table_metrics_content']):
                        pwc_html[d][t]['evaluation_table_metrics_content'] = all_data_dict['evaluation_table_metrics']

                if not convert_str_to_expr(pwc_html[d][t]['evaluation_table_data_content']) and not requested_once:
                    all_data_dict = fetch_page_details(t)
                    requested_once = True
                    pwc_html[d][t]['evaluation_table_data_content'] = all_data_dict['evaluation_table_data']
                    if not convert_str_to_expr(pwc_html[d][t]['evaluation_table_metrics_content']):
                        pwc_html[d][t]['evaluation_table_metrics_content'] = all_data_dict['evaluation_table_metrics']

                if not convert_str_to_expr(pwc_html[d][t]['evaluation_table_metrics_content']) and not requested_once:
                    all_data_dict = fetch_page_details(t)
                    requested_once = True
                    pwc_html[d][t]['evaluation_table_metrics_content'] = all_data_dict['evaluation_table_metrics']

                if not convert_str_to_expr(pwc_html[d][t]['dataset_details_content']):
                    print(d, t, " FOUND NULL STRINGS")
                    continue
                dataset_name =    convert_str_to_expr(pwc_html[d][t]['dataset_details_content'])[0]['name']
                dt_details   = convert_str_to_expr(pwc_html[d][t]['sota_page_details_content'])
                dataset_variant_name = dt_details['dataset_name']
                dataset_full_name    = f"{dataset_name}__{dataset_variant_name}"
                task_name = dt_details['task_name']
                task_main_area_name = dt_details['task_main_area_name']
                metric_script = pwc_html[d][t]['evaluation_table_metrics_content']
                if metric_script is None:
                    not_found_metrics.append(t)
                else:
                    metric_data = json.loads(metric_script)
                    # Extract values from each dictionary
                    for item in metric_data:
                        metric_dir_dict[item['name']] = item['is_loss']
                            
            except Exception as ex1:
                print("Intial parsing error: ", ex1)
        
            if not task_name in intermediate_pwc_leaderboards[dataset_full_name]:
                intermediate_pwc_leaderboards[dataset_full_name][task_name] = {'task_main_area_name': task_main_area_name, 'metric_dirs': metric_dir_dict}
            elif task_name in intermediate_pwc_leaderboards[dataset_full_name] and 'ldb' in intermediate_pwc_leaderboards[dataset_full_name][task_name]:
                continue

            dict_res = convert_str_to_expr(pwc_html[d][t]['evaluation_table_data_content'])
            # dict_res is a list of dicts where each dict contains information of each entry in ldb.

            ind_tdmm_entries_list = []
            all_metrics = []
            for i in dict_res:
                ind_tdmm_entry_dict = {}
                if 'paper' in i and 'title' in i['paper']:
                    paper_pwcurl = i['paper']['url']
                    if paper_pwcurl in pwcpageurl_arxiv_map:
                        ind_tdmm_entry_dict['arxivid'] = pwcpageurl_arxiv_map[paper_pwcurl]
                    else:
                        ind_tdmm_entry_dict['arxivid'] = get_arxivid_from_pwc(paper_pwcurl)
                        pwcpageurl_arxiv_map[paper_pwcurl] = ind_tdmm_entry_dict['arxivid']
                    ind_tdmm_entry_dict['method'] = i['method']
                    for m in i['metrics']:
                        all_metrics.append(m)
                        ind_tdmm_entry_dict[f"m_{m}"] = i['metrics'][m]
                    for rm in i['raw_metrics']:
                        ind_tdmm_entry_dict[f"rm_{rm}"] = i['raw_metrics'][rm]
                ind_tdmm_entries_list.append(ind_tdmm_entry_dict)
            all_metrics = list(set(all_metrics))

            intermediate_pwc_leaderboards[dataset_full_name][task_name]['ldb'] = ind_tdmm_entries_list
            intermediate_pwc_leaderboards[dataset_full_name][task_name]['all_metrics'] = all_metrics
            
        except Exception as ex:
            print(ex)
            print("IGNORING TASK: ", t)

    print(f"TIME:  {time.time()-start_time}")
    with open('../dataset/INTERMEDIATE_LDBS_WITH_METRICDIRS.pkl', 'wb') as intldb:
        pickle.dump(intermediate_pwc_leaderboards, intldb)
        print("File saved ...")

try:
    with open('../dataset/not_found_metrics.pkl', 'wb') as f:
        pickle.dump(not_found_metrics, f)
except Exception as ex:
    print(ex)
