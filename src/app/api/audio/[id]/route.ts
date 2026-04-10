import { NextRequest, NextResponse } from 'next/server'

const BACKEND = 'http://127.0.0.1:17493'

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const url = `${BACKEND}/audio/${id}`
  
  try {
    const res = await fetch(url)
    if (!res.ok) {
      return NextResponse.json({ error: 'Audio not found' }, { status: 404 })
    }
    const blob = await res.blob()
    const contentType = res.headers.get('content-type') || 'audio/wav'
    return new NextResponse(blob, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'no-cache',
      },
    })
  } catch {
    return NextResponse.json({ error: 'Audio not found' }, { status: 404 })
  }
}