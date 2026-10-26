import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-6 text-white">
      <div className="max-w-md text-center">
        <h1 className="text-4xl font-bold">404</h1>
        <p className="mt-4 text-slate-400">Page not found</p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-lg bg-sky-600 px-6 py-2 font-semibold hover:bg-sky-500"
        >
          Go Home
        </Link>
      </div>
    </main>
  )
}
