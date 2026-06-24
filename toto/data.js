// ============================
// 胴元設定エリア（ここを編集）
// ============================

const CONFIG = {
  administrator: "タロウ",         // 胴元の名前
  entryFee: 1000,                  // 参加費（円）
  houseEdge: 0.20,                 // 胴元取り分（20% = 0.20）
  prizeRatio: [0.50, 0.30, 0.20], // 1位・2位・3位の賞金配分
  lastUpdated: "2026-06-24",
};

// ============================
// オッズ設定（胴元が設定）
// ============================

const ODDS = [
  { team: "ブラジル",     flag: "🇧🇷", odds: 4.5,  tier: "favorite" },
  { team: "フランス",     flag: "🇫🇷", odds: 5.0,  tier: "favorite" },
  { team: "スペイン",     flag: "🇪🇸", odds: 5.5,  tier: "favorite" },
  { team: "アルゼンチン", flag: "🇦🇷", odds: 6.0,  tier: "favorite" },
  { team: "イングランド", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", odds: 7.0,  tier: "contender" },
  { team: "ドイツ",       flag: "🇩🇪", odds: 8.0,  tier: "contender" },
  { team: "ポルトガル",   flag: "🇵🇹", odds: 9.0,  tier: "contender" },
  { team: "オランダ",     flag: "🇳🇱", odds: 10.0, tier: "contender" },
  { team: "ベルギー",     flag: "🇧🇪", odds: 12.0, tier: "contender" },
  { team: "クロアチア",   flag: "🇭🇷", odds: 15.0, tier: "contender" },
  { team: "ウルグアイ",   flag: "🇺🇾", odds: 18.0, tier: "contender" },
  { team: "メキシコ",     flag: "🇲🇽", odds: 20.0, tier: "contender" },
  { team: "アメリカ",     flag: "🇺🇸", odds: 25.0, tier: "underdog" },
  { team: "日本",         flag: "🇯🇵", odds: 40.0, tier: "underdog" },
  { team: "モロッコ",     flag: "🇲🇦", odds: 35.0, tier: "underdog" },
  { team: "韓国",         flag: "🇰🇷", odds: 50.0, tier: "underdog" },
];

// ============================
// トーナメント対戦カード
// ============================

// status: "upcoming" | "live" | "done"
// winner: 勝者チーム名（doneの時のみ）

const MATCHES = [
  // ラウンド32（16試合）
  { id: "r32_1",  round: "R32", teamA: "ブラジル",     teamB: "セネガル",     scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_2",  round: "R32", teamA: "フランス",     teamB: "モロッコ",     scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_3",  round: "R32", teamA: "スペイン",     teamB: "メキシコ",     scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_4",  round: "R32", teamA: "アルゼンチン", teamB: "オーストラリア", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_5",  round: "R32", teamA: "イングランド", teamB: "スイス",       scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_6",  round: "R32", teamA: "ドイツ",       teamB: "デンマーク",   scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_7",  round: "R32", teamA: "ポルトガル",   teamB: "チュニジア",   scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_8",  round: "R32", teamA: "オランダ",     teamB: "韓国",         scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_9",  round: "R32", teamA: "ベルギー",     teamB: "カナダ",       scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_10", round: "R32", teamA: "クロアチア",   teamB: "チリ",         scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_11", round: "R32", teamA: "ウルグアイ",   teamB: "ガーナ",       scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_12", round: "R32", teamA: "アメリカ",     teamB: "ナイジェリア", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_13", round: "R32", teamA: "日本",         teamB: "ポーランド",   scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_14", round: "R32", teamA: "コロンビア",   teamB: "コートジボワール", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_15", round: "R32", teamA: "エクアドル",   teamB: "セルビア",     scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r32_16", round: "R32", teamA: "スウェーデン", teamB: "カメルーン",   scoreA: null, scoreB: null, winner: null, status: "upcoming" },

  // ラウンド16（8試合）
  { id: "r16_1", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r16_2", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r16_3", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r16_4", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r16_5", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r16_6", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r16_7", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "r16_8", round: "R16", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },

  // 準々決勝（4試合）
  { id: "qf_1", round: "QF", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "qf_2", round: "QF", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "qf_3", round: "QF", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "qf_4", round: "QF", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },

  // 準決勝（2試合）
  { id: "sf_1", round: "SF", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
  { id: "sf_2", round: "SF", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },

  // 決勝
  { id: "final", round: "Final", teamA: "TBD", teamB: "TBD", scoreA: null, scoreB: null, winner: null, status: "upcoming" },
];

// ============================
// 参加者の予想データ
// ============================

// 各参加者の予想をここに入力
// predictions: { matchId: "予想勝者チーム名", ... }

const PARTICIPANTS = [
  // 例：
  // {
  //   name: "田中太郎",
  //   paid: true,
  //   predictions: {
  //     r32_1: "ブラジル",
  //     r32_2: "フランス",
  //     // ... 全試合分
  //   }
  // },
];

// ============================
// ポイント計算設定
// ============================

const ROUND_POINTS = {
  "R32":   1,
  "R16":   2,
  "QF":    4,
  "SF":    8,
  "Final": 16,
};
