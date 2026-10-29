export default function PageHeader({ title, description, children }) {
  return <div className="page-header mb-6 flex min-w-0 flex-col justify-between gap-4 sm:flex-row sm:items-center"><div className="min-w-0"><h1 className="wrap-break-word text-2xl font-bold tracking-tight text-slate-900">{title}</h1><p className="mt-1 wrap-break-word text-sm text-slate-500">{description}</p></div>{children && <div className="flex w-full flex-wrap gap-2 sm:w-auto sm:shrink-0">{children}</div>}</div>;
}
