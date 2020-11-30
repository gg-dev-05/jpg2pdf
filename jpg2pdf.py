import requests, json, yaml
import os

def make_pdfs(links, env=""):
    # links = ["https://picsum.photos/200/300", "https://picsum.photos/200/300", "https://picsum.photos/200/300", "https://picsum.photos/200/300"]

    # dev = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
    # url_pdf = dev['pdf_maker']
    # url_merge = dev['pdf_merger']

    if env == "dev":
        dev = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
        url_pdf = dev['pdf_maker']
        url_merge = dev['pdf_merger']
        
    else:
        url_pdf = os.environ.get("pdf_maker")
        url_merge = os.environ.get("pdf_merger")
    print(url_merge, url_pdf)
    # print(links)
    links_list = []
    for i in links:
        links_list.append(i[0])
    # print(links_list)
    pdf_links = []
    for i in links_list:
        data = '{"Parameters": [{"Name": "File","FileValue": {"Url":"' + i + '"}},{"Name": "StoreFile","Value": true}]}'
        # print(data)
        output = json.loads(data)

        fin = requests.post(url_pdf, json=output)
        response = fin.json()
        print(response['Files'][0]['Url'])
        pdf_links.append(response['Files'][0]['Url'])


    data = '{"Parameters": [{"Name": "Files","FileValues": ['

    for i in range(len(pdf_links)):
        data += '{"Url": " '+ pdf_links[i] +'"}'
        if(i != len(pdf_links)-1):
            data += ","

    data += ']},{"Name": "StoreFile","Value": true}]}'

    print(data)
    output = json.loads(data)
    fin = requests.post(url_merge, json=output)
    response = fin.json()
    return response
 