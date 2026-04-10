import { NextRequest, NextResponse } from 'next/server'

const ARTICLE_API = process.env.ARTICLE_API_URL || 'http://61.153.213.238:4029/get_paper_articles'

function isValidDate(str: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(str) && !isNaN(Date.parse(str))
}

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl
  const siteId = searchParams.get('siteId') || '111'
  const docstatus = searchParams.get('docstatus') || '38'
  const beginDate = searchParams.get('beginDate')
  const endDate = searchParams.get('endDate')

  if (!/^\d+$/.test(siteId)) {
    return NextResponse.json({ error: 'Invalid siteId' }, { status: 400 })
  }
  if (!/^\d+$/.test(docstatus)) {
    return NextResponse.json({ error: 'Invalid docstatus' }, { status: 400 })
  }
  if (beginDate && !isValidDate(beginDate)) {
    return NextResponse.json({ error: 'Invalid beginDate format, expected YYYY-MM-DD' }, { status: 400 })
  }
  if (endDate && !isValidDate(endDate)) {
    return NextResponse.json({ error: 'Invalid endDate format, expected YYYY-MM-DD' }, { status: 400 })
  }

  const params = new URLSearchParams()
  params.set('siteId', siteId)
  params.set('docstatus', docstatus)
  if (beginDate) params.set('beginDate', beginDate)
  if (endDate) params.set('endDate', endDate)

  try {
    const res = await fetch(`${ARTICLE_API}?${params.toString()}`)
    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: 'Failed to fetch articles' }, { status: 502 })
  }
}
