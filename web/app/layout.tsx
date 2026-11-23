import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
  title: 'Jebickson AI — Your documents, understood',
  description: 'Search your PDFs privately in your browser and explore matching excerpts with page references. A free document intelligence project by Jebickson.',
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
