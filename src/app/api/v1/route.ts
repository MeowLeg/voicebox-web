import { NextRequest, NextResponse } from 'next/server'

const BACKEND = 'http://127.0.0.1:17493'

function parseSSE(text: string) {
  const lines = text.trim().split('\n')
  let result = null
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        result = JSON.parse(line.slice(6))
      } catch { /* skip */ }
    }
  }
  return result
}

export async function GET(req: NextRequest) {
  const path = req.nextUrl.searchParams.get('path') || ''
  const url = `${BACKEND}/${path}`
  try {
    const res = await fetch(url)
    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('text/event-stream')) {
      const text = await res.text()
      const data = parseSSE(text)
      if (data) return NextResponse.json(data)
      return NextResponse.json({ error: 'Failed to parse SSE' }, { status: 502 })
    }
    if (contentType.includes('application/json')) {
      const data = await res.json()
      return NextResponse.json(data)
    }
    const text = await res.text()
    return NextResponse.json({ error: 'Unexpected response format', detail: text.slice(0, 500) }, { status: 502 })
  } catch {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 502 })
  }
}

export async function POST(req: NextRequest) {
  const path = req.nextUrl.searchParams.get('path') || ''
  const url = `${BACKEND}/${path}`
  const contentType = req.headers.get('content-type') || ''
  
  try {
    let fetchOptions: RequestInit = { method: 'POST' }
    
    if (contentType.includes('multipart/form-data')) {
      const formData = await req.formData()
      fetchOptions.body = formData
    } else {
      const body = await req.json()
      fetchOptions.body = JSON.stringify(body)
      fetchOptions.headers = { 'Content-Type': 'application/json' }
    }
    
    const res = await fetch(url, fetchOptions)
    const resContentType = res.headers.get('content-type') || ''
    if (resContentType.includes('application/json')) {
      const data = await res.json()
      return NextResponse.json(data)
    }
    const text = await res.text()
    return NextResponse.json({ error: 'Unexpected response format', detail: text.slice(0, 500) }, { status: 502 })
  } catch (err) {
    console.error('Proxy POST error:', err)
    return NextResponse.json({ error: 'Backend unavailable', detail: err instanceof Error ? err.message : 'Unknown error' }, { status: 502 })
  }
}

export async function DELETE(req: NextRequest) {
  const path = req.nextUrl.searchParams.get('path') || ''
  const url = `${BACKEND}/${path}`
  
  try {
    const res = await fetch(url, { method: 'DELETE' })
    const resContentType = res.headers.get('content-type') || ''
    if (resContentType.includes('application/json')) {
      const data = await res.json()
      return NextResponse.json(data)
    }
    return NextResponse.json({ success: true })
  } catch (err) {
    console.error('Proxy DELETE error:', err)
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 502 })
  }
}