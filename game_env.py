import random

class HighLowEnv:
    def __init__(self, num_players=2):
        self.num_players = num_players
        self.reset()

    def reset(self):
        # 52枚のトランプを作成 (2~14, 'R' or 'B')
        suits_map = {
            'S': 'B', 'C': 'B',
            'H': 'R', 'D': 'R'
        }
        self.deck = []
        for s in ['S', 'C', 'H', 'D']:
            for num in range(2, 15):  # 2~14 (A=14)
                self.deck.append((num, suits_map[s]))
        random.shuffle(self.deck)

        self.lives = [3] * self.num_players
        self.pot = 0
        self.current_player = 0  # 0: プレイヤー, 1: AI
        self.is_color_phase = False  # 同数時、または2/Aのときの赤黒フェーズフラグ
        
        # 最初の場のカードをめくる
        self.current_card = self.deck.pop() if self.deck else (8, 'R')
        
        # 【新ルール】最初の場のカードが 2 または A の場合は、最初から色予想フェーズにする
        if self.current_card[0] == 2 or self.current_card[0] == 14:
            self.is_color_phase = True

        return self.get_state()

    def get_action_type(self):
        return 'COLOR' if self.is_color_phase else 'HIGH_LOW'

    def step(self, action):
        """
        action:
          - HIGH_LOWフェーズの場合: 0 (HIGH), 1 (LOW)
          - COLORフェーズの場合: 0 (赤), 1 (黒)
        """
        if not self.deck:
            return "山札がなくなりました", True

        current_num, current_suit = self.current_card
        next_card = self.deck.pop()
        next_num, next_suit = next_card

        p_name = "あなた" if self.current_player == 0 else "AI"
        info = ""
        done = False

        if not self.is_color_phase:
            # --- HIGH / LOW フェーズ ---
            is_correct = False
            if action == 0:  # HIGH
                if next_num > current_num:
                    is_correct = True
            else:  # LOW
                if next_num < current_num:
                    is_correct = True

            if current_num == next_num:
                # 数字が同じ場合：赤か黒かの追加予測フェーズへ
                self.current_card = next_card
                self.is_color_phase = True
                info = f"{p_name}の予想: 数字が同じ({current_num} == {next_num})！赤か黒かの追加予測を行ってください。"
            else:
                if is_correct:
                    info = f"{p_name}はハイロー予想に【成功】！ (場の:{current_num} ➔ めくった:{next_num})"
                else:
                    penalty = next_num  # めくられたカードの数字と同じ枚数のチップをポットに払う
                    self.lives[self.current_player] -= 1
                    self.pot += penalty
                    info = f"{p_name}はハイロー予想に【失敗】... 残機-1, ポットに+{penalty}枚 (場の:{current_num} ➔ めくった:{next_num})"

                # めくられたカードは次の場のカードになる
                self.current_card = next_card
                
                # 【新ルールチェック】新しくなった場のカードが 2 または A の場合、次の人の番では最初から色予想にする
                if self.current_card[0] == 2 or self.current_card[0] == 14:
                    self.is_color_phase = True
                
                # 残機チェック
                active_players = [i for i in range(self.num_players) if self.lives[i] > 0]
                if len(active_players) <= 1:
                    done = True
                else:
                    self.current_player = (self.current_player + 1) % self.num_players
        else:
            # --- COLOR（赤・黒）フェーズ ---
            chosen_color = 'R' if action == 0 else 'B'
            is_correct = (next_suit == chosen_color)

            if is_correct:
                info = f"{p_name}は赤黒予想に【成功】！色を当てました ({'赤' if next_suit=='R' else '黒'})"
            else:
                penalty = next_num
                self.lives[self.current_player] -= 1
                self.pot += penalty
                info = f"{p_name}は赤黒予想に【失敗】... 残機-1, ポットに+{penalty}枚 ({'赤' if next_suit=='R' else '黒'})"

            # 赤黒フェーズ終了、カード更新
            self.current_card = next_card
            self.is_color_phase = False

            # 【新ルールチェック】新しくなった場のカードが 2 または A の場合、次の人の番でも色予想にする
            if self.current_card[0] == 2 or self.current_card[0] == 14:
                self.is_color_phase = True

            active_players = [i for i in range(self.num_players) if self.lives[i] > 0]
            if len(active_players) <= 1:
                done = True
            else:
                self.current_player = (self.current_player + 1) % self.num_players

        # 山札切れチェック
        if len(self.deck) == 0:
            done = True

        return info, done

    def get_state(self):
        return {
            'card_num': self.current_card[0],
            'card_suit': '赤' if self.current_card[1] == 'R' else '黒',
            'action_type': self.get_action_type(),
            'lives_human': self.lives[0],
            'lives_ai': self.lives[1],
            'pot': self.pot,
            'remaining_deck': len(self.deck),
            'current_player': self.current_player,
            'is_color_phase': self.is_color_phase
        }
