'use strict';

/**
 * UIコンポーネントテンプレートライブラリ
 * カテゴリ別に17種のテンプレートを定義。
 * propFields: プロパティパネルに表示する編集可能フィールド
 */
window.TEMPLATES = [
  // =========================================================
  // ボタン
  // =========================================================
  {
    id: 'primary-button',
    name: 'Primary Button',
    category: 'ボタン',
    icon: '🔵',
    defaultSize: { width: 240, height: 64 },
    defaultProps: {
      text: 'Button', fillColor: '#3a86ff', textColor: '#ffffff',
      strokeColor: '#8ecfff', strokeWidth: 2, radius: 18, opacity: 1, fontSize: 20,
    },
    role: 'action', importance: 'primary', state: 'default',
    propFields: ['text', 'fillColor', 'textColor', 'radius', 'opacity'],
  },
  {
    id: 'secondary-button',
    name: 'Secondary Button',
    category: 'ボタン',
    icon: '⬜',
    defaultSize: { width: 200, height: 56 },
    defaultProps: {
      text: 'Cancel', fillColor: '#3a3d41', textColor: '#d4d4d4',
      strokeColor: '#6a7080', strokeWidth: 2, radius: 14, opacity: 1, fontSize: 18,
    },
    role: 'action', importance: 'secondary', state: 'default',
    propFields: ['text', 'fillColor', 'textColor', 'radius', 'opacity'],
  },
  {
    id: 'danger-button',
    name: 'Danger Button',
    category: 'ボタン',
    icon: '🔴',
    defaultSize: { width: 200, height: 56 },
    defaultProps: {
      text: 'Delete', fillColor: '#cc2233', textColor: '#ffffff',
      strokeColor: '#ff5566', strokeWidth: 2, radius: 14, opacity: 1, fontSize: 18,
    },
    role: 'action', importance: 'critical', state: 'default',
    propFields: ['text', 'fillColor', 'textColor', 'radius', 'opacity'],
  },
  {
    id: 'icon-button',
    name: 'Icon Button',
    category: 'ボタン',
    icon: '🔷',
    defaultSize: { width: 56, height: 56 },
    defaultProps: {
      text: '⚙', fillColor: '#2d2d2d', textColor: '#8ecfff',
      strokeColor: '#4b9eff', strokeWidth: 2, radius: 12, opacity: 1, fontSize: 24,
    },
    role: 'action', importance: 'secondary', state: 'default',
    propFields: ['text', 'fillColor', 'textColor', 'radius', 'opacity'],
  },

  // =========================================================
  // テキスト
  // =========================================================
  {
    id: 'title-label',
    name: 'Title Label',
    category: 'テキスト',
    icon: '𝐓',
    defaultSize: { width: 360, height: 48 },
    defaultProps: {
      text: 'Title Text', fillColor: 'transparent', textColor: '#ffffff',
      radius: 0, opacity: 1, fontSize: 32, textAlign: 'left',
    },
    role: 'text', importance: 'primary', state: 'default',
    propFields: ['text', 'textColor', 'fontSize', 'textAlign', 'opacity'],
  },
  {
    id: 'body-label',
    name: 'Body Label',
    category: 'テキスト',
    icon: '📝',
    defaultSize: { width: 320, height: 32 },
    defaultProps: {
      text: 'Body text here', fillColor: 'transparent', textColor: '#cccccc',
      radius: 0, opacity: 1, fontSize: 18, textAlign: 'left',
    },
    role: 'text', importance: 'info', state: 'default',
    propFields: ['text', 'textColor', 'fontSize', 'textAlign', 'opacity'],
  },
  {
    id: 'caption-label',
    name: 'Caption Label',
    category: 'テキスト',
    icon: '🔤',
    defaultSize: { width: 200, height: 24 },
    defaultProps: {
      text: 'Caption', fillColor: 'transparent', textColor: '#888888',
      radius: 0, opacity: 1, fontSize: 12, textAlign: 'left',
    },
    role: 'text', importance: 'muted', state: 'default',
    propFields: ['text', 'textColor', 'fontSize', 'textAlign', 'opacity'],
  },
  {
    id: 'number-label',
    name: 'Number Label',
    category: 'テキスト',
    icon: '#️⃣',
    defaultSize: { width: 120, height: 48 },
    defaultProps: {
      text: '1,234', fillColor: 'transparent', textColor: '#f1c40f',
      radius: 0, opacity: 1, fontSize: 28, textAlign: 'right',
    },
    role: 'data_display', importance: 'emphasis', state: 'default',
    propFields: ['text', 'textColor', 'fontSize', 'textAlign', 'opacity'],
  },

  // =========================================================
  // ゲージ
  // =========================================================
  {
    id: 'hp-bar',
    name: 'HP Bar',
    category: 'ゲージ',
    icon: '❤️',
    defaultSize: { width: 320, height: 28 },
    defaultProps: {
      fillColor: '#2ecc71', trackColor: '#1a2a1a',
      value: 0.75, strokeColor: 'transparent', strokeWidth: 0,
      radius: 14, opacity: 1,
    },
    role: 'progress', importance: 'info', state: 'default',
    propFields: ['fillColor', 'trackColor', 'value', 'radius', 'opacity'],
  },
  {
    id: 'mp-bar',
    name: 'MP Bar',
    category: 'ゲージ',
    icon: '💧',
    defaultSize: { width: 280, height: 20 },
    defaultProps: {
      fillColor: '#3a86ff', trackColor: '#0f1a2a',
      value: 0.6, strokeColor: 'transparent', strokeWidth: 0,
      radius: 10, opacity: 1,
    },
    role: 'progress', importance: 'info', state: 'default',
    propFields: ['fillColor', 'trackColor', 'value', 'radius', 'opacity'],
  },
  {
    id: 'cooldown-wheel',
    name: 'Cooldown Wheel',
    category: 'ゲージ',
    icon: '🔄',
    defaultSize: { width: 72, height: 72 },
    defaultProps: {
      fillColor: '#a855f7', trackColor: '#1a1a2a',
      value: 0.3, strokeColor: '#c084fc', strokeWidth: 2,
      radius: 36, opacity: 1,
    },
    role: 'progress', importance: 'info', state: 'cooldown',
    propFields: ['fillColor', 'trackColor', 'value', 'opacity'],
    visualType: 'radial',
  },

  // =========================================================
  // フィードバック
  // =========================================================
  {
    id: 'badge-count',
    name: 'Badge Count',
    category: 'フィードバック',
    icon: '🔴',
    defaultSize: { width: 40, height: 40 },
    defaultProps: {
      text: '3', fillColor: '#e74c3c', textColor: '#ffffff',
      strokeColor: '#ff7070', strokeWidth: 2,
      radius: 20, opacity: 1, fontSize: 18,
    },
    role: 'badge', importance: 'critical', state: 'default',
    propFields: ['text', 'fillColor', 'textColor', 'radius', 'opacity'],
  },
  {
    id: 'status-tag',
    name: 'Status Tag',
    category: 'フィードバック',
    icon: '🏷️',
    defaultSize: { width: 100, height: 32 },
    defaultProps: {
      text: 'NEW', fillColor: '#f39c12', textColor: '#ffffff',
      strokeColor: 'transparent', strokeWidth: 0,
      radius: 6, opacity: 1, fontSize: 14,
    },
    role: 'badge', importance: 'emphasis', state: 'default',
    propFields: ['text', 'fillColor', 'textColor', 'radius', 'opacity'],
  },
  {
    id: 'toast-label',
    name: 'Toast / Notification',
    category: 'フィードバック',
    icon: '📣',
    defaultSize: { width: 480, height: 56 },
    defaultProps: {
      text: 'ミッション完了！ +500 EXP', fillColor: '#1a3a1a', textColor: '#7fff7f',
      strokeColor: '#2ecc71', strokeWidth: 2,
      radius: 8, opacity: 1, fontSize: 16,
    },
    role: 'feedback', importance: 'info', state: 'success',
    propFields: ['text', 'fillColor', 'textColor', 'radius', 'opacity'],
  },

  // =========================================================
  // コンテナ
  // =========================================================
  {
    id: 'card-panel',
    name: 'Card Panel',
    category: 'コンテナ',
    icon: '🃏',
    defaultSize: { width: 360, height: 200 },
    defaultProps: {
      fillColor: '#252526', textColor: '#d4d4d4',
      strokeColor: '#3c3f41', strokeWidth: 2,
      radius: 16, opacity: 1,
    },
    role: 'container', importance: 'secondary', state: 'default',
    propFields: ['fillColor', 'strokeColor', 'strokeWidth', 'radius', 'opacity'],
  },
  {
    id: 'modal-panel',
    name: 'Modal Panel',
    category: 'コンテナ',
    icon: '🪟',
    defaultSize: { width: 600, height: 380 },
    defaultProps: {
      fillColor: '#1e1e2e', textColor: '#d4d4d4',
      strokeColor: '#4b9eff', strokeWidth: 2,
      radius: 20, opacity: 1,
    },
    role: 'modal', importance: 'primary', state: 'default',
    propFields: ['fillColor', 'strokeColor', 'strokeWidth', 'radius', 'opacity'],
  },
  {
    id: 'toggle-switch',
    name: 'Toggle Switch',
    category: 'コントロール',
    icon: '🔘',
    defaultSize: { width: 80, height: 40 },
    defaultProps: {
      fillColor: '#2ecc71', trackColor: '#3a3a3a',
      value: 1, strokeColor: 'transparent', strokeWidth: 0,
      radius: 20, opacity: 1,
    },
    role: 'toggle', importance: 'secondary', state: 'on',
    propFields: ['fillColor', 'trackColor', 'opacity'],
    visualType: 'toggle',
  },
];

/**
 * IDでテンプレートを検索
 */
window.getTemplate = function(id) {
  return window.TEMPLATES.find(t => t.id === id) || null;
};

/**
 * カテゴリ別にグループ化
 */
window.getTemplatesByCategory = function() {
  const categories = {};
  for (const t of window.TEMPLATES) {
    if (!categories[t.category]) categories[t.category] = [];
    categories[t.category].push(t);
  }
  return categories;
};
