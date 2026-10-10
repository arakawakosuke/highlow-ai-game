import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
from game_env import HighLowEnv

# 1. Qネットワーク（ニューラルネットワーク）の定義
class QNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(QNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

    def forward(self, x):
        return self.fc(x)

# 2. 学習メイン処理
def train():
    env = HighLowEnv(num_players=2)
    state_dim = 6          # 状態ベクトルの要素数 (game_env.py の _get_observation で定義したもの)
    action_dim = 2         # 行動の選択肢 (0: HIGH/RED, 1: LOW/BLACK)

    # ネットワークとオプティマイザの設定
    policy_net = QNetwork(state_dim, action_dim)
    target_net = QNetwork(state_dim, action_dim)
    target_net.load_state_dict(policy_net.state_dict())

    optimizer = optim.Adam(policy_net.parameters(), lr=0.001)
    memory = deque(maxlen=10000)

    # ハイパーパラメータ
    gamma = 0.95
    epsilon = 1.0
    epsilon_min = 0.05
    epsilon_decay = 0.995
    batch_size = 32

    episodes = 1000
    print("--- ハイローAI（DQN）の学習を開始します ---")

    for episode in range(1, episodes + 1):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            # ε-greedy法による行動選択
            if random.random() < epsilon:
                action = random.choice([0, 1])
            else:
                with torch.no_grad():
                    state_t = torch.FloatTensor(state).unsqueeze(0)
                    q_values = policy_net(state_t)
                    action = q_values.argmax().item()

            next_state, reward, done, _ = env.step(action)
            memory.append((state, action, reward, next_state, done))
            state = next_state
            total_reward += reward

            # リプレイバッファからランダムにバッチを取り出して学習
            if len(memory) >= batch_size:
                batch = random.sample(memory, batch_size)
                s_batch, a_batch, r_batch, ns_batch, d_batch = zip(*batch)

                s_t = torch.FloatTensor(np.array(s_batch))
                a_t = torch.LongTensor(a_batch).unsqueeze(1)
                r_t = torch.FloatTensor(r_batch).unsqueeze(1)
                ns_t = torch.FloatTensor(np.array(ns_batch))
                d_t = torch.FloatTensor(d_batch).unsqueeze(1)

                # Q値の計算
                q_vals = policy_net(s_t).gather(1, a_t)
                with torch.no_grad():
                    max_next_q = target_net(ns_t).max(1)[0].unsqueeze(1)
                    target_q = r_t + (1 - d_t) * gamma * max_next_q

                # 損失計算とパラメータ更新
                loss = nn.MSELoss()(q_vals, target_q)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        # ランダム行動率（イプシロン）を下げる
        if epsilon > epsilon_min:
            epsilon *= epsilon_decay

        # 定期的にターゲットネットワークを更新
        if episode % 10 == 0:
            target_net.load_state_dict(policy_net.state_dict())

        # 進捗の表示
        if episode % 100 == 0:
            print(f"Episode {episode}/{episodes} | Total Reward: {total_reward:.1f} | Epsilon: {epsilon:.2f}")

    print("--- 学習が完了しました ---")
    
    # 学習したモデルを保存
    torch.save(policy_net.state_dict(), "highlow_dqn.pth")
    print("モデルを 'highlow_dqn.pth' として保存しました！")

if __name__ == "__main__":
    train()
