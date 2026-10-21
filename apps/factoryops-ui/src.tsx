import React from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function App() {
  const unifiedUrl = `${window.location.protocol}//${window.location.hostname}:5173/quality`;

  React.useEffect(() => {
    window.location.replace(unifiedUrl);
  }, [unifiedUrl]);

  return (
    <main>
      <section className="grid" style={{ maxWidth: 760, margin: '10vh auto' }}>
        <article className="hero">
          <span className="eyebrow">FACTORYOPS AI</span>
          <h1>正在进入统一工作台</h1>
          <p>质量异常处置已经并入 SupplyGuard AI 主站。</p>
          <a href={unifiedUrl}>如果没有自动跳转，请点击这里</a>
        </article>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
