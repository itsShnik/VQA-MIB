from openvqa.datasets.vqa.eval.vqa import VQA
from openvqa.datasets.vqa.eval.vqaEval import VQAEval
import json, pickle
import numpy as np
import wandb
from urllib import request, parse
import json

def send_message_to_slack(text):

    post = {"text": "{0}".format(text)}

    try:
        json_data = json.dumps(post)

        req = request.Request("https://hooks.slack.com/services/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",
                              data=json_data.encode('ascii'),
                              headers={'Content-Type': 'application/json'})
        resp = request.urlopen(req)
    except Exception as em:
        print("EXCEPTION: " + str(em))

def eval(__C, dataset, ans_ix_list, pred_list, result_eval_file, ensemble_file, log_file, valid=False):
    result_eval_file = result_eval_file + '.json'

    qid_list = [ques['question_id'] for ques in dataset.ques_list]
    ans_size = dataset.ans_size

    result = [{
        'answer': dataset.ix_to_ans[str(ans_ix_list[qix])],
        # 'answer': dataset.ix_to_ans[ans_ix_list[qix]],
        'question_id': int(qid_list[qix])
    } for qix in range(qid_list.__len__())]

    if __C.USE_NEW_QUESTION == "True":
        print("")
        print("Answer for the asked question is: ", result)
        print("")

    print('Save the result to file: {}'.format(result_eval_file))
    json.dump(result, open(result_eval_file, 'w'))

    if __C.TEST_SAVE_PRED:
        print('Save the prediction vector to file: {}'.format(ensemble_file))

        pred_list = np.array(pred_list).reshape(-1, ans_size)
        result_pred = [{
            'pred': pred_list[qix],
            'qid': int(qid_list[qix])
        } for qix in range(qid_list.__len__())]

        pickle.dump(result_pred, open(ensemble_file, 'wb+'), protocol=-1)


    if valid:
        # create vqa object and vqaRes object
        ques_file_path = __C.RAW_PATH[__C.DATASET][__C.SPLIT['val']]
        ans_file_path = __C.RAW_PATH[__C.DATASET][__C.SPLIT['val'] + '-anno']

        vqa = VQA(ans_file_path, ques_file_path)
        vqaRes = vqa.loadRes(result_eval_file, ques_file_path)

        # create vqaEval object by taking vqa and vqaRes
        vqaEval = VQAEval(vqa, vqaRes, n=2)  # n is precision of accuracy (number of places after decimal), default is 2

        # evaluate results
        """
        If you have a list of question ids on which you would like to evaluate your results, pass it as a list to below function
        By default it uses all the question ids in annotation file
        """
        vqaEval.evaluate()

        # print accuracies
        print("\n")
        print("Overall Accuracy is: %.02f\n" % (vqaEval.accuracy['overall']))
        slack_message = "Model: %s Epoch: %d\n" % (__C.VERSION, int(__C.current_epoch))
 
        # print("Per Question Type Accuracy is the following:")
        # for quesType in vqaEval.accuracy['perQuestionType']:
        #     print("%s : %.02f" % (quesType, vqaEval.accuracy['perQuestionType'][quesType]))
        # print("\n")
        print("Per Answer Type Accuracy is the following:")
        for ansType in vqaEval.accuracy['perAnswerType']:
            print("%s : %.02f" % (ansType, vqaEval.accuracy['perAnswerType'][ansType]))
            slack_message += "%s : %.02f\n" % (ansType, vqaEval.accuracy['perAnswerType'][ansType])
        print("\n")

        send_message_to_slack(slack_message)
        print('Write to log file: {}'.format(log_file))
        logfile = open(log_file, 'a+')

        logfile.write("Overall Accuracy is: %.02f\n" % (vqaEval.accuracy['overall']))
        wandb.log({"Overall Accuracy": vqaEval.accuracy['overall']})
        for ansType in vqaEval.accuracy['perAnswerType']:
            logfile.write("%s : %.02f " % (ansType, vqaEval.accuracy['perAnswerType'][ansType]))
            wandb.log({ansType: vqaEval.accuracy['perAnswerType'][ansType]})
        logfile.write("\n\n")
        logfile.close()


