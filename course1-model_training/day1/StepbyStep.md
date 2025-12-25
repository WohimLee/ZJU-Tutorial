## Step by Step


### 1 登录服务器
#### 1.1 VSCode 安装插件
![alt text](imgs/image.png)

#### 1.2 配置 SSH 服务

```sh
Host AutoDL-5090-Traning    # 自命名
    HostName connect.westd.seetacloud.com   # IP 地址
    Port 41664  # 端口号
    User root   # 用户名
```

#### 1.3 设置免密登录
![alt text](imgs/no_passwd.png)


### 2 搭建 Llama-Factory 环境
- 官网: https://github.com/hiyouga/LLaMA-Factory

#### 2.1 创建独立的 Conda 环境

```sh
conda create -n llama-factory python=3.10

git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory

conda activate llama-factory
pip install -e ".[torch,metrics]" --no-build-isolation
```

