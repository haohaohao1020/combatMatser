#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格斗大师 - 主游戏模块
整合所有模块，实现完整的游戏循环
"""

import pygame
import sys
from typing import Optional

# 从其他模块导入
from config import (
    GameState, CharacterState,
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GROUND_Y,
    PLAYER_WIDTH, PLAYER_HEIGHT, ROUND_TIME, MAX_ROUNDS,
    clamp, WHITE, BLACK
)
from character import Character
from attack import (
    get_light_attack, get_heavy_attack, get_low_attack
)
from ai import AIController, add_ai_to_character
from effects import EffectManager, ScreenShake
from ui import UI, InGameMenu
from menu import MainMenu
from stage import Stage


# =============================================================================
# 游戏主类
# =============================================================================
class Game:
    """格斗大师游戏主类"""
    
    def __init__(self):
        # 初始化pygame
        pygame.init()
        pygame.font.init()
        
        # 创建窗口
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Combat Master - 格斗大师")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # ========================================
        # 游戏状态
        # ========================================
        self.state = GameState.MENU
        self.game_mode = "pvp"  # "pvp" 或 "pvc"
        self.difficulty = "easy"
        
        # ========================================
        # 回合数据
        # ========================================
        self.round_timer = ROUND_TIME
        self.round_timer_frames = 0
        self.p1_wins = 0
        self.p2_wins = 0
        self.current_round = 1
        
        # ========================================
        # 回合过渡效果
        # ========================================
        self.round_transition = False
        self.round_transition_timer = 0
        self.round_transition_text = ""
        
        # ========================================
        # 游戏对象
        # ========================================
        self.player1: Optional[Character] = None
        self.player2: Optional[Character] = None
        self.ai_controller: Optional[AIController] = None
        self.stage = Stage()
        self.effect_manager = EffectManager()
        self.screen_shake = ScreenShake()
        
        # ========================================
        # UI和菜单
        # ========================================
        self.ui = UI()
        self.main_menu = MainMenu()
        self.ingame_menu = InGameMenu()
        
        # 初始化字体
        self.ui.init_fonts()
        self.main_menu.init_fonts()
        self.ingame_menu.init_fonts()
        
        # 设置主菜单
        self.main_menu.set_menu("main")
    
    # =========================================================================
    # 开始新回合
    # =========================================================================
    def start_new_round(self):
        """开始新回合"""
        ground_y = GROUND_Y - PLAYER_HEIGHT
        
        # 创建玩家
        self.player1 = Character(200, ground_y, is_player1=True)
        self.player2 = Character(SCREEN_WIDTH - 260, ground_y, is_player1=False)
        
        # 如果是PVC模式，为玩家2添加AI
        if self.game_mode == "pvc":
            self.ai_controller = add_ai_to_character(self.player2, self.difficulty)
        else:
            self.ai_controller = None
        
        # 重置计时器
        self.round_timer = ROUND_TIME
        self.round_timer_frames = 0
        self.effect_manager.clear()
        self.screen_shake = ScreenShake()
        
        # 回合开始过渡效果
        self.round_transition = True
        self.round_transition_timer = 120
        self.round_transition_text = f"ROUND {self.current_round}"
    
    # =========================================================================
    # 开始游戏
    # =========================================================================
    def start_game(self):
        """开始新游戏"""
        self.current_round = 1
        self.p1_wins = 0
        self.p2_wins = 0
        self.start_new_round()
        self.state = GameState.PLAYING
    
    # =========================================================================
    # 检查回合结束
    # =========================================================================
    def check_round_end(self) -> bool:
        """
        检查回合是否结束
        
        Returns:
            True 表示回合结束
        """
        if not self.player1 or not self.player2:
            return False
        
        p1_dead = self.player1.health <= 0
        p2_dead = self.player2.health <= 0
        time_up = self.round_timer <= 0
        
        if p1_dead or p2_dead or time_up:
            # 决定胜利者
            if p1_dead and not p2_dead:
                winner = 2
            elif p2_dead and not p1_dead:
                winner = 1
            else:
                # 时间结束，比较血量
                if self.player1.health > self.player2.health:
                    winner = 1
                elif self.player2.health > self.player1.health:
                    winner = 2
                else:
                    winner = 0  # 平局
            
            # 更新胜利计数和显示文字
            if winner == 1:
                self.p1_wins += 1
                self.round_transition_text = "PLAYER 1 WINS!"
            elif winner == 2:
                self.p2_wins += 1
                if self.game_mode == "pvc":
                    self.round_transition_text = "CPU WINS!"
                else:
                    self.round_transition_text = "PLAYER 2 WINS!"
            else:
                self.round_transition_text = "DRAW!"
            
            # 设置过渡效果
            self.round_transition = True
            self.round_transition_timer = 180
            self.state = GameState.ROUND_END
            return True
        
        return False
    
    # =========================================================================
    # 检查游戏结束
    # =========================================================================
    def check_game_over(self) -> bool:
        """
        检查游戏是否结束（三局两胜）
        
        Returns:
            True 表示游戏结束
        """
        if self.p1_wins >= 2:
            self.state = GameState.GAME_OVER
            return True
        elif self.p2_wins >= 2:
            self.state = GameState.GAME_OVER
            return True
        return False
    
    # =========================================================================
    # 处理玩家输入
    # =========================================================================
    def handle_player_input(self, keys):
        """
        处理玩家的游戏输入（非菜单输入）
        
        Args:
            keys: pygame.key.get_pressed() 的结果
        """
        if not self.player1 or not self.player2:
            return
        
        # ========================================
        # 重置状态
        # ========================================
        p1_move_input = 0
        p2_move_input = 0
        
        self.player1.is_blocking = False
        self.player2.is_blocking = False
        
        # ========================================
        # 玩家1输入
        # ========================================
        # 受击硬直中无法操作
        if self.player1.hitstun <= 0 and self.player1.grounded_timer <= 0:
            if self.player1.dodge_timer <= 0:
                if not self.player1.is_attacking:
                    if not self.player1.is_ultimate:
                        # 移动
                        if keys[pygame.K_a]:
                            p1_move_input = -1
                        if keys[pygame.K_d]:
                            p1_move_input = 1
                        
                        # 跳跃
                        if keys[pygame.K_w] and self.player1.jump_count < self.player1.max_jumps:
                            self.player1.jump()
                        
                        # 下蹲
                        if keys[pygame.K_s]:
                            self.player1.state = CharacterState.CROUCH
                            self.player1.block_high = False
                        
                        # 攻击
                        if keys[pygame.K_j]:
                            self.player1.start_attack(get_light_attack())
                        if keys[pygame.K_k]:
                            self.player1.start_attack(get_heavy_attack())
                        
                        # 格挡
                        if keys[pygame.K_l]:
                            if self.player1.is_grounded:
                                self.player1.is_blocking = True
                                self.player1.state = CharacterState.BLOCK
                                if keys[pygame.K_s]:
                                    self.player1.block_high = False
                                else:
                                    self.player1.block_high = True
                        
                        # 必杀
                        if keys[pygame.K_SPACE] and self.player1.rage >= self.player1.max_rage:
                            self.player1.start_ultimate()
                        
                        # 闪避
                        if keys[pygame.K_LSHIFT] and self.player1.dodge_cooldown <= 0:
                            dodge_dir = -self.player1.facing if p1_move_input == 0 else p1_move_input
                            self.player1.start_dodge(dodge_dir)
        
        # ========================================
        # 玩家2输入（如果是PVP模式）
        # ========================================
        if self.game_mode == "pvp":
            if self.player2.hitstun <= 0 and self.player2.grounded_timer <= 0:
                if self.player2.dodge_timer <= 0:
                    if not self.player2.is_attacking:
                        if not self.player2.is_ultimate:
                            # 移动
                            if keys[pygame.K_LEFT]:
                                p2_move_input = -1
                            if keys[pygame.K_RIGHT]:
                                p2_move_input = 1
                            
                            # 跳跃
                            if keys[pygame.K_UP] and self.player2.jump_count < self.player2.max_jumps:
                                self.player2.jump()
                            
                            # 下蹲
                            if keys[pygame.K_DOWN]:
                                self.player2.state = CharacterState.CROUCH
                                self.player2.block_high = False
                            
                            # 攻击
                            if keys[pygame.K_KP1] or keys[pygame.K_1]:
                                self.player2.start_attack(get_light_attack())
                            if keys[pygame.K_KP2] or keys[pygame.K_2]:
                                self.player2.start_attack(get_heavy_attack())
                            
                            # 格挡
                            if keys[pygame.K_KP3] or keys[pygame.K_3]:
                                if self.player2.is_grounded:
                                    self.player2.is_blocking = True
                                    self.player2.state = CharacterState.BLOCK
                                    if keys[pygame.K_DOWN]:
                                        self.player2.block_high = False
                                    else:
                                        self.player2.block_high = True
                            
                            # 必杀
                            if keys[pygame.K_RETURN] and self.player2.rage >= self.player2.max_rage:
                                self.player2.start_ultimate()
                            
                            # 闪避
                            if keys[pygame.K_RSHIFT] and self.player2.dodge_cooldown <= 0:
                                dodge_dir = -self.player2.facing if p2_move_input == 0 else p2_move_input
                                self.player2.start_dodge(dodge_dir)
        
        # ========================================
        # 应用移动
        # ========================================
        # 玩家1移动
        if not self.player1.is_blocking and not self.player1.is_attacking:
            if self.player1.hitstun <= 0 and self.player1.dodge_timer <= 0:
                if p1_move_input != 0:
                    from config import WALK_SPEED
                    self.player1.vel_x = p1_move_input * WALK_SPEED
                    if self.player1.state != CharacterState.JUMP and self.player1.is_grounded:
                        self.player1.state = CharacterState.WALK
                else:
                    if self.player1.is_grounded and self.player1.state == CharacterState.WALK:
                        self.player1.state = CharacterState.IDLE
        
        # 玩家2移动（PVP模式）
        if self.game_mode == "pvp":
            if not self.player2.is_blocking and not self.player2.is_attacking:
                if self.player2.hitstun <= 0 and self.player2.dodge_timer <= 0:
                    if p2_move_input != 0:
                        from config import WALK_SPEED
                        self.player2.vel_x = p2_move_input * WALK_SPEED
                        if self.player2.state != CharacterState.JUMP and self.player2.is_grounded:
                            self.player2.state = CharacterState.WALK
                    else:
                        if self.player2.is_grounded and self.player2.state == CharacterState.WALK:
                            self.player2.state = CharacterState.IDLE
    
    # =========================================================================
    # 事件处理
    # =========================================================================
    def handle_events(self):
        """处理所有游戏事件"""
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        # 窗口关闭事件
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
        
        # ========================================
        # 菜单状态
        # ========================================
        if self.state == GameState.MENU:
            self.main_menu.update()
            selection = self.main_menu.handle_input(keys, events)
            
            if selection is not None:
                if self.main_menu.menu_type == "main":
                    if selection == 0:
                        self.main_menu.set_menu("mode")
                    elif selection == 1:
                        self.running = False
                
                elif self.main_menu.menu_type == "mode":
                    if selection == 0:
                        self.game_mode = "pvp"
                        self.start_game()
                    elif selection == 1:
                        self.game_mode = "pvc"
                        self.main_menu.set_menu("difficulty")
                    elif selection == 2:
                        self.main_menu.set_menu("main")
                
                elif self.main_menu.menu_type == "difficulty":
                    if selection == 0:
                        self.difficulty = "easy"
                        self.start_game()
                    elif selection == 1:
                        self.difficulty = "hard"
                        self.start_game()
                    elif selection == 2:
                        self.main_menu.set_menu("mode")
        
        # ========================================
        # 游戏中状态
        # ========================================
        elif self.state == GameState.PLAYING:
            # ESC暂停
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED
                        self.ingame_menu.selected_index = 0
            
            # 处理玩家输入（调用角色的handle_input方法）
            if self.player1 and self.player2:
                self.player1.handle_input(keys, self.player2)
                self.player2.handle_input(keys, self.player1)
            
            # AI更新（如果是PVC模式）
            if self.ai_controller and self.player1:
                self.ai_controller.update(self.player1)
        
        # ========================================
        # 暂停状态
        # ========================================
        elif self.state == GameState.PAUSED:
            selection = self.ingame_menu.handle_input(keys, events)
            
            if selection is not None:
                if selection == 0:
                    self.state = GameState.PLAYING
                elif selection == 1:
                    self.start_game()
                elif selection == 2:
                    self.state = GameState.MENU
                    self.main_menu.set_menu("main")
        
        # ========================================
        # 游戏结束状态
        # ========================================
        elif self.state == GameState.GAME_OVER:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.state = GameState.MENU
                        self.main_menu.set_menu("main")
    
    # =========================================================================
    # 游戏更新
    # =========================================================================
    def update(self):
        """更新游戏状态"""
        
        # ========================================
        # 游戏中更新
        # ========================================
        if self.state == GameState.PLAYING:
            # 回合计时器
            self.round_timer_frames += 1
            if self.round_timer_frames >= FPS:
                self.round_timer_frames = 0
                if self.round_timer > 0:
                    self.round_timer -= 1
            
            # 回合过渡效果
            if self.round_transition:
                self.round_transition_timer -= 1
                if self.round_transition_timer <= 0:
                    self.round_transition = False
            else:
                # 更新玩家
                if self.player1 and self.player2:
                    self.player1.update(self.player2)
                    self.player2.update(self.player1)
                    
                    # 攻击判定
                    self.player1.check_attack_hit(
                        self.player2, 
                        self.effect_manager.effects,
                        self.screen_shake
                    )
                    self.player2.check_attack_hit(
                        self.player1, 
                        self.effect_manager.effects,
                        self.screen_shake
                    )
                
                # 更新特效
                self.effect_manager.update()
                
                # 更新屏幕震动
                self.screen_shake.update()
                
                # 更新场景
                self.stage.update()
                
                # 检查回合结束
                if not self.check_round_end():
                    pass
        
        # ========================================
        # 回合结束状态
        # ========================================
        elif self.state == GameState.ROUND_END:
            self.round_transition_timer -= 1
            if self.round_transition_timer <= 0:
                if not self.check_game_over():
                    # 进入下一回合
                    self.current_round += 1
                    self.start_new_round()
                    self.state = GameState.PLAYING
        
        # ========================================
        # 菜单状态
        # ========================================
        elif self.state == GameState.MENU:
            self.main_menu.update()
            self.stage.update()
    
    # =========================================================================
    # 渲染
    # =========================================================================
    def render(self):
        """渲染游戏画面"""
        self.screen.fill(BLACK)
        
        shake_x, shake_y = self.screen_shake.get_offset()
        
        # ========================================
        # 菜单状态
        # ========================================
        if self.state == GameState.MENU:
            self.stage.render(self.screen)
            self.main_menu.render(self.screen)
        
        # ========================================
        # 游戏中、暂停、回合结束状态
        # ========================================
        elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.ROUND_END]:
            # 渲染场景（带震动）
            self.stage.render(self.screen, shake_x, shake_y)
            
            # 渲染玩家
            if self.player1 and self.player2:
                self.player1.render(self.screen, shake_x, shake_y)
                self.player2.render(self.screen, shake_x, shake_y)
            
            # 渲染特效
            self.effect_manager.render(self.screen, shake_x, shake_y)
            
            # 渲染UI（不受震动影响）
            if self.player1 and self.player2:
                # 玩家1血条
                self.ui.render_health_bar(
                    self.screen, 50, 30, 280, 30,
                    self.player1.health, self.player1.max_health,
                    True, self.player1.rage, self.player1.max_rage,
                    "PLAYER 1"
                )
                
                # 玩家2血条
                p2_name = "PLAYER 2" if self.game_mode == "pvp" else "CPU"
                self.ui.render_health_bar(
                    self.screen, SCREEN_WIDTH - 330, 30, 280, 30,
                    self.player2.health, self.player2.max_health,
                    False, self.player2.rage, self.player2.max_rage,
                    p2_name
                )
                
                # 计时器
                self.ui.render_timer(self.screen, self.round_timer)
                
                # 回合分数
                self.ui.render_round_score(self.screen, self.p1_wins, self.p2_wins)
                
                # 连击
                self.ui.render_combo(self.screen, self.player1, self.player2)
            
            # 回合过渡效果
            if self.round_transition:
                # 计算alpha
                alpha = 0
                if self.round_transition_timer > 100:
                    alpha = int((120 - self.round_transition_timer) / 20 * 255)
                elif self.round_transition_timer > 30:
                    alpha = 255
                else:
                    alpha = int(self.round_transition_timer / 30 * 255)
                
                self.ui.render_round_transition(
                    self.screen, 
                    self.round_transition_text, 
                    alpha
                )
        
        # ========================================
        # 暂停菜单
        # ========================================
        if self.state == GameState.PAUSED:
            self.ingame_menu.render_pause(self.screen)
        
        # ========================================
        # 游戏结束结算
        # ========================================
        if self.state == GameState.GAME_OVER and self.player1 and self.player2:
            winner_is_p1 = self.p1_wins >= 2
            
            if winner_is_p1:
                winner_name = "PLAYER 1"
            else:
                winner_name = "CPU" if self.game_mode == "pvc" else "PLAYER 2"
            
            self.ingame_menu.render_game_over(
                self.screen,
                winner_name,
                self.player1.max_combo,
                self.player2.max_combo,
                self.player1.total_damage_dealt,
                self.player2.total_damage_dealt,
                winner_is_p1
            )
        
        # 刷新显示
        pygame.display.flip()
    
    # =========================================================================
    # 游戏主循环
    # =========================================================================
    def run(self):
        """运行游戏主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


# =============================================================================
# 主函数
# =============================================================================
def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
