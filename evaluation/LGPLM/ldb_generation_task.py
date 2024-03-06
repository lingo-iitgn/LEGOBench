import json
from vllm import LLM, SamplingParams
import argparse
import pandas as pd

model_name_map = {"meta-llama/Llama-2-7b-chat-hf": "llama2_7b_chat", "meta-llama/Llama-2-13b-chat-hf": "llama2_13b_chat", "meta-llama/Llama-2-7b-hf": "llama2_7b", "meta-llama/Llama-2-13b-hf": "llama2_13b", "mistralai/Mistral-7B-v0.1": "mistral_7b", "mistralai/Mistral-7B-Instruct-v0.1": "mistral_7b_instruct", "lmsys/vicuna-13b-v1.5": "vicuna_13b", "lmsys/vicuna-7b-v1.5": "vicuna_7b", "HuggingFaceH4/zephyr-7b-beta": "zephyr_7b_beta", "tiiuae/falcon-7b": "falcon_7b", "tiiuae/falcon-7b-instruct": "falcon_7b_instruct", "facebook/galactica-6.7b": "galactica_7b"}

model2contextlength = {
    "meta-llama/Llama-2-7b-chat-hf": ("llama2_7b_chat", 4096, "https://huggingface.co/meta-llama/Llama-2-7b-chat-hf/blob/main/generation_config.json"),
    "meta-llama/Llama-2-13b-chat-hf": ("llama2_13b_chat", 4096, "https://huggingface.co/meta-llama/Llama-2-13b-chat-hf/blob/main/generation_config.json"), 
    "meta-llama/Llama-2-7b-hf": ("llama2_7b", 4096, "https://huggingface.co/meta-llama/Llama-2-7b-hf/blob/main/generation_config.json"),
    "meta-llama/Llama-2-13b-hf": ("llama2_13b", 4096, "https://huggingface.co/meta-llama/Llama-2-13b-hf/blob/main/generation_config.json"),
    "mistralai/Mistral-7B-v0.1": ("mistral_7b", 8000, "https://aws.amazon.com/blogs/machine-learning/mistral-7b-foundation-models-from-mistral-ai-are-now-available-in-amazon-sagemaker-jumpstart/#:~:text=Mistral%207B%20has%20an%208%2C000,at%20a%207B%20model%20size."),
    "mistralai/Mistral-7B-Instruct-v0.1": ("mistral_7b_instruct", 8000, "https://www.secondstate.io/articles/mistral-7b-instruct-v0.1/"),
    "mistralai/Mistral-7B-Instruct-v0.2": ("mistral_7b_instruct_v2", 8000, "https://www.secondstate.io/articles/mistral-7b-instruct-v0.1/"), 
    "lmsys/vicuna-13b-v1.5": ("vicuna_13b", 4096, "https://huggingface.co/lmsys/vicuna-13b-v1.5/blob/main/generation_config.json"),
    "lmsys/vicuna-7b-v1.5": ("vicuna_7b", 4096, "https://huggingface.co/lmsys/vicuna-7b-v1.5/blob/main/generation_config.json"),
    "HuggingFaceH4/zephyr-7b-beta": ("zephyr_7b_beta", 16384, "https://docs.endpoints.anyscale.com/supported-models/huggingfaceh4-zephyr-7b-beta/"),
    "tiiuae/falcon-7b": ("falcon_7b", 2048, "https://huggingface.co/tiiuae/falcon-7b/blob/main/tokenizer_config.json"),
    "tiiuae/falcon-7b-instruct": ("falcon_7b_instruct", 2048, "https://huggingface.co/tiiuae/falcon-7b-instruct/blob/main/tokenizer_config.json"), 
    "facebook/galactica-6.7b": ("galactica_7b", 2048, "https://llm.extractum.io/model/facebook%2Fgalactica-6.7b,11ptgQY4r8q8sc7KY9iN38"),
}

def model_response_gen(model_name):
    if model_name in ["mistralai/Mistral-7B-v0.1", "mistralai/Mistral-7B-Instruct-v0.1", "tiiuae/falcon-7b", "tiiuae/falcon-7b-instruct", "HuggingFaceH4/zephyr-7b-beta"]:
        llm = LLM(model=model_name, tensor_parallel_size=1, dtype="half")
    else:
        llm = LLM(model=model_name, tensor_parallel_size=1)
    model_tokenizer = llm.get_tokenizer()
    model_max_len = model2contextlength[model_name][1]
    clean_model_name = model_name_map[model_name]

    model_ans_list = []
    prompts_list = []
    
    # Read the qa data
    with open("retriever/longdocdata/qa.json", "r") as f:
        qa_data = json.load(f)

    with open("retriever/output_data/retrieved_paragraphs_10_bm25.json", "r") as fin:
        topk_src_paras = json.load(fin)

    for _, dockey in enumerate(qa_data):
        # if _ > 10:
        #     break
        ldb_gen_prompt = "You are provided with a dataset, task, and metric. You need to create a leaderboard which lists the performance of various methods on the provided dataset and task using the provided metric. Excerpts from research papers are provided above which report the performance of methods on these task, dataset and metric. Extract the performance from the excerpt to create the leaderboard. The output should be a single table listing each method and performance only. Do not include any explanation or additional text in the output, only include method name and performance scores. " + qa_data[dockey]["question"] + " Output:"
        
        prompt_len = len(model_tokenizer.tokenize(ldb_gen_prompt))
        topk_paras_text = "Excerpt: "
        doc_path = "retriever" + dockey[1:]
        with open(doc_path, "r") as srcfin:
            src_text_paras = json.load(srcfin)
        for paraid_score_entry in topk_src_paras[dockey]["retrieved_paragraphs"]:
            topk_paras_text += src_text_paras["paragraphs"][paraid_score_entry[0]] + " "
        topk_paras_text = topk_paras_text.strip()
        topk_paras_text += "\n"
        
        context_tokens_list = model_tokenizer.tokenize(topk_paras_text)
        if (len(context_tokens_list) + prompt_len) < model_max_len:
            ldb_gen_prompt = topk_paras_text + ldb_gen_prompt
        else:
            croppped_context = model_tokenizer.convert_tokens_to_string(context_tokens_list[:(model_max_len-prompt_len-3)])
            ldb_gen_prompt = croppped_context + ldb_gen_prompt

        prompts_list.append(ldb_gen_prompt)
        local_dict = {'prompt': ldb_gen_prompt, 'GT': qa_data[dockey]["answer"]}
        model_ans_list.append(local_dict)
    
    print("Collated all ldb generation prompts, now generating outputs...")
    sampling_params = SamplingParams(temperature=0.1, top_p=0.95, max_tokens=1600, stop=['Question:', '\n\n\n\n', '| --- | --- | --- | --- | --- | ', '| | | |'])
    prompt_list_chunks = [prompts_list[x:x+500] for x in range(0, len(prompts_list), 500)]

    generated_rank_list = []
    global_ctr = 0
    for prmpt_chunk in prompt_list_chunks:
        outputs = llm.generate(prmpt_chunk, sampling_params)
        # print("Finished generation...")
        for output in outputs:
            generated_rank_list.append(output.outputs[0].text)

        for _, ranks in enumerate(generated_rank_list):
            model_ans_list[_][f'{clean_model_name}_ldb'] = ranks

        df = pd.DataFrame(model_ans_list)
        df.to_excel(f'data/llm_responses/{clean_model_name}.xlsx')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', choices=list(model_name_map.keys()), help='name of the model to use for generation, specifically the hf repo name')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    model_response_gen(args.model_name)
