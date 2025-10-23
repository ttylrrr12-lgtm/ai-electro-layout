export function exportSVG(plan:any, symbols:any[], routes:Record<string,{points:number[][]}[]>) {
  const w = 1200, h = 900
  const s = 0.1 // масштаб (мм→px)
  const wallPaths = plan.walls.map((w:any)=>`M ${w.x1*s} ${w.y1*s} L ${w.x2*s} ${w.y2*s}`).join(' ')
  const routePaths = Object.values(routes).flat().map(p=>{
    const d = p.points.map((pt,i)=> (i? 'L':'M') + ' ' + (pt[0]*s) + ' ' + (pt[1]*s)).join(' ')
    return `<path d="${d}" stroke="#c60" stroke-width="2" fill="none" />`
  }).join('\n')
  const symbolsSvg = symbols.map(smb=>`<circle cx="${smb.x*s}" cy="${smb.y*s}" r="4" fill="${smb.type==='panel' ? '#0a0':'#06c'}"/>`).join('\n')
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}">
  <g stroke="#222" stroke-width="2" fill="none">
    <path d="${wallPaths}" />
  </g>
  ${routePaths}
  ${symbolsSvg}
</svg>`
}
