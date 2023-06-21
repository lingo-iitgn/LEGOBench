import os
os.environ['CUDA_VISIBLE_DEVICES'] = "1"

import torch
import pickle
from datetime import datetime
from transformers import AutoModel, AutoTokenizer
from cogdl.oag import oagbert

def load_specter():
    tokenizer   = AutoTokenizer.from_pretrained('allenai/specter')
    model       = AutoModel.from_pretrained('allenai/specter')
    return tokenizer, model

def load_scibert():
    tokenizer   = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased')
    model       = AutoModel.from_pretrained('allenai/scibert_scivocab_uncased')
    return tokenizer, model

def load_scincl():
    tokenizer   = AutoTokenizer.from_pretrained('malteos/scincl')
    model       = AutoModel.from_pretrained('malteos/scincl')
    return tokenizer, model

def load_oagbert():
    tokenizer, model = oagbert()
    return tokenizer,model

def get_model(mname):
    if mname == 'specter':
        tokenizer, model = load_specter()
    elif mname == 'scincl':
        tokenizer, model = load_scincl()
    elif mname == 'scibert':
        tokenizer, model = load_scibert()
    elif mname == 'oagbert':
        tokenizer, model = load_oagbert()
    else:
        raise NotImplementedError("Models are: specter, scincl, scibert, oagbert")
    return tokenizer, model



def encode_batch_wise(model, tokenizer, document_list, to_save_loc, batch_size=20):
    device = torch.device("cuda")
    model.to(device)
    model.eval()

    doc_batch_list = []
    batch_ids = []

    document_emb_dict = {}

    for _, d in enumerate(document_list):
        if _ % 2000 == 0:
            print("Encoded: {} @ {}".format(_, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            if len(document_emb_dict) > 0:
                with open(to_save_loc, 'ab') as femb:
                    pickle.dump(document_emb_dict, femb)
                    document_emb_dict = {}
        
        # document_list is actually a dictionatry. org_pid_seq is not provided
        doc_batch_list.append((document_list[d].get('title').strip() or '') + " " + tokenizer.sep_token + " " + (document_list[d].get('abstract').strip() or ''))
        batch_ids.append(d)

        if _%batch_size == 0:
            inputs = tokenizer(doc_batch_list, padding=True, truncation=True, return_tensors="pt", max_length=512)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                result = model(**inputs)
                embeddings = result[1] 

            for ii, k in enumerate(batch_ids):
                document_emb_dict[k] = embeddings[ii].cpu().detach().numpy()

            doc_batch_list = []
            batch_ids = []

    if batch_ids:
        inputs = tokenizer(doc_batch_list, padding=True, truncation=True, return_tensors="pt", max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            result = model(**inputs)
            embeddings = result[1] 

        for _, k in enumerate(batch_ids):
            document_emb_dict[k] = embeddings[_].cpu().detach().numpy()
    
    with open(to_save_loc, 'ab') as f:
        pickle.dump(document_emb_dict, f)

    return document_emb_dict


if __name__ == "__main__":
    with open('data/tabs/tabs_data.pkl', 'rb') as f:
        tabs_data = pickle.load(f)

    for mname in ['oagbert', 'specter', 'scibert', 'scincl']:
        tokenizer, model = get_model(mname)
        encode_batch_wise(model, tokenizer, tabs_data, to_save_loc=f'./data/tabs/emb_{mname}.pkl', batch_size=8)