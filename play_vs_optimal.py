import random
from collections import Counter
from game_env import HighLowEnv

class OptimalDecisionAI:
    """数式に基づいて毎ターン完全な期待値計算を行う最適AI"""
    
    def choose_action(self, current_card, deck):
        curr_num, curr_suit = current_card
        total_remaining = len(deck)

        if total_remaining == 0:
            return 0

        # 行動タイプの判定 (2 or A は色予想)
        if curr_num == 2 or curr_num == 14:
            # 赤と黒の残り枚数をカウントして多い方を選択
            red_count = sum(1 for n, s in deck if s == 'R')
            black_count = total_remaining - red_count
            
            # 0: RED(赤), 1: BLACK(黒)
            chosen = 0 if red_count >= black_count else 1
            reason = f"赤の残り{red_count}枚 / 黒の残り{black_count}枚 -> {'赤' if chosen==0 else '黒'}を選択"
            return chosen, reason

        else:
            # HIGH / LOW の確率・ペナルティ期待値計算
            counts = Counter([n for n, s in deck])

            high_win_cards = sum(counts[n] for n in range(curr_num + 1, 15))
            low_win_cards = sum(counts[n] for n in range(2, curr_num))

            p_high = high_win_cards / total_remaining
            p_low = low_win_cards / total_remaining

            # 失敗時の平均損失額（ペナルティ期待値）
            low_cards_sum = sum(n * counts[n] for n in range(2, curr_num))
            penalty_if_high_fails = low_cards_sum / total_remaining if low_win_cards > 0 else 0

            high_cards_sum = sum(n * counts[n] for n in range(curr_num + 1, 15))
            penalty_if_low_fails = high_cards_sum / total_remaining if high_win_cards > 0 else 0

            # 評価関数 (期待値)
            ev_high = (p_high * 1.0) - penalty_if_high_fails
            ev_low = (p_low * 1.0) - penalty_if_low_fails

            chosen = 0 if ev_high >= ev_low else 1
            reason = (f"HIGH勝率:{p_high*100:.1f}%(EV:{ev_high:.2f}) vs "
                      f"LOW勝率:{p_low*100:.1f}%(EV:{ev_low:.2f}) -> {'HIGH' if chosen==0 else 'LOW'}を選択")
            return chosen, reason

def play():
    env = HighLowEnv(num_players=2)
    ai = OptimalDecisionAI()

    human_p = 0
    done = False

    print("\n=======================================================")
    print("   🧠 あなた vs 数学最適戦略AI - ハイロー対戦スタート 🧠")
    print("=======================================================\n")

    while not done:
        curr_p = env.current_player
        card_num, card_suit = env.current_card
        action_type = env.get_action_type()

        suit_str = "赤" if card_suit == 'R' else "黒"
        print(f"\n-------------------------------------------------------")
        print(f"現在の場: [{card_num}] ({suit_str}) | 山札残り: {len(env.deck)}枚 | ポット: {env.pot}枚")
        print(f"残機 -> あなた(P1): {env.lives[0]} | 最適AI(P2): {env.lives[1]}")

        if curr_p == human_p:
            print("\n👉 あなたの番です！")
            if action_type == 'HIGH_LOW':
                choice = input("予想を選んでください (0: HIGH, 1: LOW): ").strip()
                action = int(choice) if choice in ['0', '1'] else 0
            else:
                choice = input("【2またはAが出ました】色を選んでください (0: 赤/RED, 1: 黒/BLACK): ").strip()
                action = int(choice) if choice in ['0', '1'] else 0
        else:
            print("\n🤖 AIの思考中...")
            action, reason = ai.choose_action(env.current_card, env.deck)
            print(f"AIの思考ログ: {reason}")

        # ゲーム進行
        next_state, reward, done, info = env.step(action)
        print(f"【結果】: {info}")

    print("\n=======================================================")
    print("                      ゲーム終了")
    active = [i for i in range(2) if env.lives[i] > 0]
    if active:
        winner = active[0]
        if winner == human_p:
            print("🎉 あなたの勝利！最適AIを撃破しました！すごい！")
        else:
            print("🤖 最適AIの勝利！精密な計算の勝利です。")
    else:
        print("🤝 引き分け（山札切れ）でした。")
    print("=======================================================\n")

if __name__ == "__main__":
    play()
