import { NextRequest, NextResponse } from 'next/server'

const ARTICLE_DETAIL_API = process.env.ARTICLE_API_URL || 'http://61.153.213.238:4029/get_paper_article_detail'

export async function GET(req: NextRequest) {
  const metadataId = req.nextUrl.searchParams.get('metadataId')
  if (!metadataId) {
    return NextResponse.json({ error: 'metadataId is required' }, { status: 400 })
  }
  if (!/^\d+$/.test(metadataId)) {
    return NextResponse.json({ error: 'Invalid metadataId' }, { status: 400 })
  }

  try {
    const res = await fetch(`${ARTICLE_DETAIL_API}?metadataId=${metadataId}`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: 'Failed to fetch article detail' }, { status: 502 })
  }
}
