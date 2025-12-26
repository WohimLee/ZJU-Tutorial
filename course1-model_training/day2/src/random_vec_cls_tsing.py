
import os
import torch
import numpy as np
import torch.nn as nn

from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))


'''
[unk]  [pad]
collate_fn 的实现
'''

def read_data(file, num=None):

    titles = []
    labels = []
    with open(file, "r", encoding="utf-8") as f:
        data = f.read().strip().split("\n")[:num]

    for item in data:
        title, label = item.split("\t")
        titles.append(title)
        labels.append(int(label))

    return titles, labels


def build_vocab(corpus):
    vocab = {"[unk]": 0, "[pad]": 1}
    for line in corpus:
        for token in line:
            vocab.setdefault(token, len(vocab))
    return vocab, list(vocab)


class THUCNews(Dataset):
    def __init__(self, titles, labels):
        self.titles = titles
        self.labels = labels

    def __getitem__(self, idx):
        inputs = convert_tokens_to_ids(self.titles[idx])
        labels = self.labels[idx]
        return inputs, labels
    
    def __len__(self):
        return len(self.labels)


def convert_tokens_to_ids(tokens):
    ids = [vocab.get(token, vocab["[unk]"]) for token in tokens]
    return ids


def collate_fn(batch):
    batch_inputs, batch_labels = zip(*batch)

    new_batch_inputs = []
    for item in batch_inputs:
        item = item[:seq_len]
        pad_num = seq_len - len(item)
        item += [0]*pad_num
        new_batch_inputs.append(item)
    # return torch.tensor(new_batch_inputs), torch.tensor(batch_labels)
    return {
        "batch_inputs": torch.tensor(new_batch_inputs),
        "batch_labels": torch.tensor(batch_labels)
    }



class Model(nn.Module):
    def __init__(self, in_features, classes):
        super().__init__()
        self.emb = torch.randn(size=(in_features, 64))
        self.W1  = nn.Linear(in_features=64, out_features=256)
        self.W2  = nn.Linear(in_features=256, out_features=128)

        self.cls = nn.Linear(in_features=128, out_features=classes)


    def forward(self, X):
        emb = self.emb[X]
        output = self.W1(emb)
        output = self.W2(output)
        output = self.cls(output)
        return output
    
def run_valid(valid_loader):

    model.eval()

    with torch.no_grad():
        total_loss = 0
        total_correct = 0
        for batch in tqdm(valid_loader):
            batch_inputs = batch["batch_inputs"]
            batch_labels = batch["batch_labels"]

            output = model.forward(X=batch_inputs)
            output = torch.mean(output, dim=1)
            batch_avg_loss = loss_fn(output, batch_labels)

            total_loss += batch_avg_loss

            probabilities = torch.softmax(output, dim=1)
            pred_classes = torch.argmax(probabilities, dim=1)

            total_correct += torch.sum(pred_classes == batch_labels)
            
    return total_loss / len(valid_loader), total_correct / len(valid_loader.dataset)


if __name__ == "__main__":
    train_txt = os.path.join(PROJECT_ROOT, "data", "tsinghua-news/train.txt")
    valid_txt = os.path.join(PROJECT_ROOT, "data", "tsinghua-news/test.txt")
    train_titles, train_labels = read_data(train_txt, num=None)
    valid_titles, valid_labels = read_data(valid_txt)

    # 构建词典/字典，字->ID，ID->字
    vocab, idx2word = build_vocab(train_titles)

    # 文本转向量
    train_set = THUCNews(train_titles, train_labels)
    valid_set = THUCNews(valid_titles, valid_labels)

    # 数据加载器
    train_loader = DataLoader(train_set, batch_size=32, collate_fn=collate_fn, shuffle=True)
    valid_loader = DataLoader(valid_set, batch_size=8, collate_fn=collate_fn, shuffle=False)

    lengths = [len(title) for title in train_titles]
    print("标题数量:", len(lengths))
    print("平均长度:", np.mean(lengths))
    print("最大长度:", np.max(lengths))
    print("90% 分位数:", np.percentile(lengths, 90))
    print("95% 分位数:", np.percentile(lengths, 95))
    print("99% 分位数:", np.percentile(lengths, 99))

    seq_len = 25
    num_features = len(vocab) # embedding_dim
    classes = len(set(train_labels))

    model = Model(in_features=num_features, classes=classes)
    optim = torch.optim.Adam(model.parameters(), lr=0.001)

    loss_fn = nn.CrossEntropyLoss()


    epochs = 10
    
    for e in range(epochs):

        total_loss = 0

        for batch in tqdm(train_loader):
            batch_inputs = batch["batch_inputs"]
            batch_labels = batch["batch_labels"]

            output = model.forward(X=batch_inputs)
            output = torch.mean(output, dim=1)
            batch_avg_loss = loss_fn(output, batch_labels)

            total_loss += batch_avg_loss
            batch_avg_loss.backward()
            optim.step()
            optim.zero_grad()
        valid_loss, acc = run_valid(valid_loader)
        print("Epoch: {}, Loss: {}, Valid Loss: {}, Acc: {:.2f}%".format(
            e, total_loss/len(train_loader), valid_loss, acc*100
            ))
    pass




    pass