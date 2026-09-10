import React from 'react';

export function SplitPane({ leftContent, rightContent }) {
  return (
    <main className="app-layout">
      <section className="left-panel">{leftContent}</section>
      <section className="right-panel">{rightContent}</section>
    </main>
  );
}

export default SplitPane;
