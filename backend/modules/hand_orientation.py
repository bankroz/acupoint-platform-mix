"""
手掌/手背朝向判断模块。
基于 MediaPipe Hands 关键点的空间关系判断手部朝向。
"""

from schemas.models import HandLandmarks, HandOrientation


def judge_hand_orientation(hand: HandLandmarks) -> HandOrientation:
    """
    判断手部朝向：palm / back_of_hand / side / unknown。
    
    算法（启发式）：
    - 手掌：拇指与小指分居两侧 + 中指 MCP 在手腕上方（Y轴更小）
    - 手背：拇指与小指 MCP 距离压缩 + 关节可见性模式
    - 侧面：手掌法向近似 90°
    
    MediaPipe Hands 21 关键点索引：
    0: wrist, 1: thumb_cmc, 2: thumb_mcp, 3: thumb_ip, 4: thumb_tip
    5: index_mcp, 6: index_pip, 7: index_dip, 8: index_tip
    9: middle_mcp, 10: middle_pip, 11: middle_dip, 12: middle_tip
    13: ring_mcp, 14: ring_pip, 15: ring_dip, 16: ring_tip
    17: pinky_mcp, 18: pinky_pip, 19: pinky_dip, 20: pinky_tip
    """
    reasons: list[str] = []

    if len(hand.landmarks) < 21:
        return HandOrientation(
            hand_id=hand.hand_id,
            orientation="unknown",
            confidence=0.0,
            reasons=["insufficient_landmarks"],
        )

    def get(idx: int):
        return hand.landmarks[idx]

    # 关键点
    wrist = get(0)
    thumb_mcp = get(2)
    thumb_tip = get(4)
    index_mcp = get(5)
    middle_mcp = get(9)
    middle_tip = get(12)
    pinky_mcp = get(17)
    ring_mcp = get(13)

    # --- 手掌/手背判断 ---
    # 主要判断：手腕到中指的向量 vs 拇指到小指的叉积方向
    # 简化：拇指向外、小指向外 → 手掌；拇指和小指都靠拢 → 手背
    
    # 拇指与小指的 X 轴距离
    thumb_pinky_width = abs(thumb_mcp.x - pinky_mcp.x)

    # 中指 MCP 与手腕的相对位置
    middle_wrist_x = middle_mcp.x - wrist.x
    middle_wrist_y = middle_mcp.y - wrist.y

    # 拇指相对中指位置
    thumb_relative_x = thumb_mcp.x - middle_mcp.x

    # 判断逻辑
    if thumb_pinky_width > 0.08:  # 拇指和小指展开
        # 进一步判断是手掌还是手背
        # 手掌时，拇指在手的左侧（右手）或右侧（左手）
        if hand.hand_id == "right_hand":
            if thumb_mcp.x < middle_mcp.x:
                # 右手掌心朝前时，拇指在左侧
                reasons.append("thumb_pinky_spread")
                reasons.append("thumb_left_of_middle_right_hand")
                return HandOrientation(
                    hand_id=hand.hand_id,
                    orientation="palm",
                    confidence=0.7,
                    reasons=reasons,
                )
            else:
                reasons.append("thumb_pinky_spread")
                reasons.append("thumb_right_of_middle_right_hand_possible_back")
                return HandOrientation(
                    hand_id=hand.hand_id,
                    orientation="back_of_hand",
                    confidence=0.6,
                    reasons=reasons,
                )
        else:  # left_hand
            if thumb_mcp.x > middle_mcp.x:
                reasons.append("thumb_pinky_spread")
                reasons.append("thumb_right_of_middle_left_hand")
                return HandOrientation(
                    hand_id=hand.hand_id,
                    orientation="palm",
                    confidence=0.7,
                    reasons=reasons,
                )
            else:
                reasons.append("thumb_pinky_spread")
                reasons.append("thumb_left_of_middle_left_hand_possible_back")
                return HandOrientation(
                    hand_id=hand.hand_id,
                    orientation="back_of_hand",
                    confidence=0.6,
                    reasons=reasons,
                )

    elif thumb_pinky_width > 0.04:
        # 半展开 → 侧面
        reasons.append("thumb_pinky_partial_spread")
        return HandOrientation(
            hand_id=hand.hand_id,
            orientation="side",
            confidence=0.5,
            reasons=reasons,
        )
    else:
        # 收拢 → 不确定
        reasons.append("hand_closed_or_ambiguous")
        return HandOrientation(
            hand_id=hand.hand_id,
            orientation="unknown",
            confidence=0.3,
            reasons=reasons,
        )
