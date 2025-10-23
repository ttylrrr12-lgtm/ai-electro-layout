import React, { useRef, useState } from 'react'
import { exportSVG } from './lib/export'

type Wall = { x1:number,y1:number,x2:number,y2:number }
type Door = { x:number,y:number,w:number }
type Symbol = { type:'socket'|'switch'|'light'|'panel'|'junction', x:number,y:number, rotation?:number }

export default function App(){
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [plan, setPlan] = useState<{walls:Wall[],doors:Door[]}>({walls:[],doors:[]})
  const [symbols, setSymbols] = useState<Symbol[]>([])
  const [routes, setRoutes] = useState<Record<string,{points:number[][]}[]>>({})

  const draw = () => {
    const c = canvasRef.current; if (!c) return
    const ctx = c.getContext('2d')!; ctx.clearRect(0,0,c.width,c.height)
    ctx.lineWidth = 2; ctx.strokeStyle = '#222'
    // стены
    plan.walls.forEach(w=>{
      ctx.beginPath(); ctx.moveTo(w.x1/10, w.y1/10); ctx.lineTo(w.x2/10, w.y2/10); ctx.stroke()
    })
    // символы
    symbols.forEach(s=>{
      ctx.beginPath()
      ctx.arc(s.x/10, s.y/10, 4, 0, Math.PI*2)
      ctx.fillStyle = s.type==='panel' ? '#0a0' : '#06c'
      ctx.fill()
    })
    // маршруты
    Object.values(routes).flat().forEach(p=>{
      ctx.beginPath()
      p.points.forEach((pt,i)=>{
        if (i===0) ctx.moveTo(pt[0]/10, pt[1]/10)
        else ctx.lineTo(pt[0]/10, pt[1]/10)
      })
      ctx.strokeStyle = '#c60'; ctx.lineWidth = 2; ctx.stroke()
    })
  }

  React.useEffect(draw, [plan, symbols, routes])

  const loadDemo = () => {
    const demo = {
      walls:[
        {x1:0,y1:0,x2:4000,y2:0},
        {x1:4000,y1:0,x2:4000,y2:3000},
        {x1:4000,y1:3000,x2:0,y2:3000},
        {x1:0,y1:3000,x2:0,y2:0},
        {x1:2000,y1:0,x2:2000,y2:3000}
      ],
      doors:[{x:2000,y:3000,w:900}]
    }
    setPlan(demo)
    setSymbols([
      {type:'panel', x:100, y:1500},
      {type:'socket', x:3800, y:2600},
      {type:'light', x:1000, y:500},
      {type:'switch', x:2100, y:2800}
    ])
  }

  const callRoute = async () => {
    const body = {
      plan,
      detection: { symbols },
      ruleset: 'NEC2023'
    }
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/route`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body)
    })
    const data = await res.json()
    setRoutes(data.routes || {})
    alert(data.warnings?.join('\n') || 'OK')
  }

  const saveSVG = () => {
    const svg = exportSVG(plan, symbols, routes)
    const blob = new Blob([svg], {type:'image/svg+xml'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'layout.svg'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{display:'grid', gridTemplateColumns:'320px 1fr', height:'100vh', fontFamily:'Inter, system-ui, sans-serif'}}>
      <div style={{padding:16, borderRight:'1px solid #eee', display:'flex', flexDirection:'column', gap:12}}>
        <h3>AI Electro Layout</h3>
        <button onClick={loadDemo}>Загрузить демо‑план</button>
        <button onClick={callRoute}>AI‑разводка</button>
        <button onClick={saveSVG}>Экспорт SVG</button>
        <p style={{fontSize:12, color:'#666'}}>Редактирование: демо. Интегрируйте импорт PNG/PDF/SVG и детекцию символов.</p>
      </div>
      <div style={{display:'grid', placeItems:'center'}}>
        <canvas ref={canvasRef} width={800} height={600} style={{border:'1px solid #ddd', background:'#fff'}}/>
      </div>
    </div>
  )
}
