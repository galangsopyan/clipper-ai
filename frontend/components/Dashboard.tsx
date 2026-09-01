"use client";

import { motion } from "framer-motion";
import {
  Activity,
  ArrowUpRight,
  Clapperboard,
  Clock3,
  Download,
  FileVideo,
  Flame,
  FolderOpen,
  LayoutDashboard,
  Menu,
  Play,
  Settings,
  Sparkles,
  Subtitles,
  Upload,
  X,
} from "lucide-react";

import { useState } from "react";

const clips = [
  {
    id: 1,
    score: 56.07,
    type: "INSIGHT",
    start: "47:07",
    duration: "55s",
    title:
      "Lebih bagus. Mereka nggak ngiri. Dan teknologinya lebih canggih.",
    video: "/clips/clip_01_vertical.mp4",
  },
  {
    id: 2,
    score: 55.97,
    type: "VIRAL",
    start: "21:39",
    duration: "59s",
    title:
      "Tipikal Pak Prabowo itu memang kadang-kadang orangnya welas asih.",
    video: "/clips/clip_02_vertical.mp4",
  },
  {
    id: 3,
    score: 54.91,
    type: "VIRAL",
    start: "19:23",
    duration: "51s",
    title:
      "Kenapa kita kerjasama dengan UMKM juga. Jadi saling dapat.",
    video: "/clips/clip_03_vertical.mp4",
  },
  {
    id: 4,
    score: 53.29,
    type: "INSIGHT",
    start: "43:56",
    duration: "45s",
    title:
      "Dia mau di jalan raya. Saya bilang kenapa di dalam gang?",
    video: "/clips/clip_04_vertical.mp4",
  },
  {
    id: 5,
    score: 52.68,
    type: "INSIGHT",
    start: "01:11",
    duration: "60s",
    title:
      "Kita tahu bahwa banyak teman-teman minoritas yang saat ini sudah siap-siap.",
    video: "/clips/clip_05_vertical.mp4",
  },
];

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      className="rounded-2xl border border-white/[0.07] bg-white/[0.035] p-5 backdrop-blur-xl"
    >
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.06]">
        <Icon size={19} className="text-violet-300" />
      </div>

      <p className="text-sm text-zinc-500">{label}</p>

      <p className="mt-1 text-2xl font-semibold tracking-tight text-white">
        {value}
      </p>
    </motion.div>
  );
}

function ClipCard({
  clip,
  index,
  onOpen,
}: {
  clip: (typeof clips)[number];
  index: number;
  onOpen: (clip: (typeof clips)[number]) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      whileHover={{ y: -5 }}
      className="group overflow-hidden rounded-3xl border border-white/[0.08] bg-zinc-900/70 shadow-2xl shadow-black/20"
    >
      <div className="relative aspect-[9/14] overflow-hidden bg-zinc-950">
        <video
          src={clip.video}
          className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.025]"
          muted
          playsInline
          preload="metadata"
        />

        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/30" />

        <div className="absolute left-3 top-3 flex items-center gap-2">
          <div className="rounded-full border border-white/10 bg-black/60 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur-xl">
            #{clip.id}
          </div>

          <div className="rounded-full border border-orange-400/20 bg-orange-500/15 px-3 py-1.5 text-xs font-semibold text-orange-300 backdrop-blur-xl">
            {clip.type}
          </div>
        </div>

        <div className="absolute right-3 top-3 rounded-full border border-white/10 bg-black/60 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur-xl">
          {clip.score.toFixed(1)}
        </div>

        <button
          onClick={() => onOpen(clip)}
          className="absolute left-1/2 top-1/2 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white text-black opacity-0 shadow-2xl transition group-hover:opacity-100"
        >
          <Play size={20} fill="currentColor" />
        </button>

        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="mb-3 flex items-center gap-3 text-xs text-zinc-300">
            <span>{clip.start}</span>
            <span>•</span>
            <span>{clip.duration}</span>
            <span>•</span>
            <span>9:16</span>
          </div>

          <h3 className="line-clamp-3 text-sm font-medium leading-6 text-white">
            {clip.title}
          </h3>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-white/[0.06] p-3">
        <button
          onClick={() => onOpen(clip)}
          className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-zinc-300 transition hover:bg-white/[0.06] hover:text-white"
        >
          <Play size={14} />
          Preview
        </button>

        <button className="flex h-9 w-9 items-center justify-center rounded-xl text-zinc-400 transition hover:bg-white/[0.06] hover:text-white">
          <Download size={15} />
        </button>
      </div>
    </motion.div>
  );
}

export default function Dashboard() {
  const [mobileMenu, setMobileMenu] = useState(false);
  const [selectedClip, setSelectedClip] =
    useState<(typeof clips)[number] | null>(null);

  return (
    <main className="min-h-screen overflow-hidden bg-[#08080b] text-white">
      {/* Ambient background */}

      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-[15%] top-[-200px] h-[500px] w-[500px] rounded-full bg-violet-600/10 blur-[140px]" />
        <div className="absolute right-[-100px] top-[30%] h-[450px] w-[450px] rounded-full bg-blue-600/[0.06] blur-[140px]" />
      </div>

      {/* NAVBAR */}

      <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#08080b]/75 backdrop-blur-2xl">
        <div className="mx-auto flex h-18 max-w-[1500px] items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg shadow-violet-500/20">
              <Clapperboard size={20} />
            </div>

            <div>
              <div className="text-sm font-bold tracking-tight">
                CLIPFORGE
              </div>

              <div className="text-[10px] font-medium tracking-[0.22em] text-zinc-600">
                AI VIDEO ENGINE
              </div>
            </div>
          </div>

          <nav className="hidden items-center gap-1 md:flex">
            <button className="flex items-center gap-2 rounded-xl bg-white/[0.07] px-4 py-2.5 text-sm font-medium text-white">
              <LayoutDashboard size={16} />
              Dashboard
            </button>

            <button className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm text-zinc-500 transition hover:bg-white/[0.05] hover:text-white">
              <FolderOpen size={16} />
              Projects
            </button>

            <button className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm text-zinc-500 transition hover:bg-white/[0.05] hover:text-white">
              <Clapperboard size={16} />
              Clips
            </button>
          </nav>

          <div className="flex items-center gap-2">
            <button className="hidden h-10 w-10 items-center justify-center rounded-xl border border-white/[0.07] text-zinc-400 transition hover:bg-white/[0.05] hover:text-white sm:flex">
              <Settings size={17} />
            </button>

            <button
              onClick={() => setMobileMenu(!mobileMenu)}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.07] text-zinc-400 md:hidden"
            >
              {mobileMenu ? <X size={18} /> : <Menu size={18} />}
            </button>

            <div className="hidden h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-blue-500 text-xs font-bold sm:flex">
              GF
            </div>
          </div>
        </div>

        {mobileMenu && (
          <div className="border-t border-white/[0.06] p-4 md:hidden">
            <div className="space-y-1">
              {["Dashboard", "Projects", "Clips", "Settings"].map((item) => (
                <button
                  key={item}
                  className="w-full rounded-xl px-4 py-3 text-left text-sm text-zinc-400 hover:bg-white/[0.05] hover:text-white"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* CONTENT */}

      <div className="mx-auto max-w-[1500px] px-5 py-8 lg:px-8 lg:py-10">
        {/* HERO */}

        <section className="relative overflow-hidden rounded-[32px] border border-white/[0.08] bg-gradient-to-br from-violet-500/[0.12] via-white/[0.025] to-blue-500/[0.05] p-7 lg:p-10">
          <div className="absolute right-[-80px] top-[-140px] h-[350px] w-[350px] rounded-full bg-violet-600/15 blur-[100px]" />

          <div className="relative max-w-3xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-500/10 px-3 py-1.5 text-xs font-medium text-violet-300">
              <Sparkles size={13} />
              AI POWERED VIDEO CLIPPING
            </div>

            <h1 className="max-w-3xl text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl lg:text-6xl">
              Turn long podcasts into
              <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-blue-400 bg-clip-text text-transparent">
                {" "}
                viral clips.
              </span>
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-7 text-zinc-400">
              Upload your podcast and let ClipForge AI find the strongest
              moments, generate vertical videos, and burn subtitles
              automatically.
            </p>

            <div className="mt-7 flex flex-wrap gap-3">
              <button className="flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-zinc-200">
                <Upload size={17} />
                Upload Podcast
              </button>

              <button className="flex items-center gap-2 rounded-xl border border-white/[0.1] bg-white/[0.04] px-5 py-3 text-sm font-medium text-white transition hover:bg-white/[0.08]">
                <FolderOpen size={17} />
                View Projects
              </button>
            </div>
          </div>
        </section>

        {/* STATS */}

        <section className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard icon={Clock3} label="Podcast Duration" value="57:12" />
          <StatCard icon={Activity} label="Transcript Segments" value="1,835" />
          <StatCard icon={Flame} label="Viral Candidates" value="20" />
          <StatCard icon={Clapperboard} label="Generated Clips" value="5" />
        </section>

        {/* PROJECT */}

        <section className="mt-10">
          <div className="mb-4 flex items-end justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-violet-400">
                Current Project
              </p>

              <h2 className="mt-1 text-2xl font-semibold tracking-tight">
                Podcast.mp4
              </h2>
            </div>

            <span className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-300 sm:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Processed
            </span>
          </div>

          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-5">
            <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/10">
                  <FileVideo className="text-violet-300" size={22} />
                </div>

                <div>
                  <p className="font-medium text-white">Podcast.mp4</p>

                  <p className="mt-1 text-xs text-zinc-500">
                    57:12 • Indonesian • 640×360
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <Subtitles size={15} />
                Subtitles generated
              </div>
            </div>
          </div>
        </section>

        {/* TOP CLIPS */}

        <section className="mt-12">
          <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <div className="flex items-center gap-2">
                <Flame size={18} className="text-orange-400" />

                <p className="text-xs font-medium uppercase tracking-[0.2em] text-orange-400">
                  AI Selection
                </p>
              </div>

              <h2 className="mt-2 text-3xl font-semibold tracking-tight">
                Top 5 Viral Clips
              </h2>

              <p className="mt-2 text-sm text-zinc-500">
                Moments dengan potensi engagement tertinggi.
              </p>
            </div>

            <button className="flex items-center gap-2 self-start rounded-xl border border-white/[0.07] px-4 py-2.5 text-xs font-medium text-zinc-300 transition hover:bg-white/[0.05] hover:text-white sm:self-auto">
              View all candidates
              <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {clips.map((clip, index) => (
              <ClipCard
                key={clip.id}
                clip={clip}
                index={index}
                onOpen={setSelectedClip}
              />
            ))}
          </div>
        </section>
      </div>

      {/* MODAL */}

      {selectedClip && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-5 backdrop-blur-xl"
          onClick={() => setSelectedClip(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-white/[0.1] bg-zinc-950 md:flex-row"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedClip(null)}
              className="absolute right-4 top-4 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-black/60 text-zinc-300 backdrop-blur-xl transition hover:bg-white/10 hover:text-white"
            >
              <X size={18} />
            </button>

            <div className="flex max-h-[65vh] items-center justify-center bg-black md:w-1/2 md:max-h-[90vh]">
              <video
                src={selectedClip.video}
                controls
                autoPlay
                className="max-h-[65vh] w-full object-contain md:max-h-[90vh]"
              />
            </div>

            <div className="flex flex-1 flex-col justify-between p-7 md:p-9">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-semibold text-violet-300">
                    #{selectedClip.id}
                  </span>

                  <span className="rounded-full bg-orange-500/10 px-3 py-1 text-xs font-semibold text-orange-300">
                    {selectedClip.type}
                  </span>
                </div>

                <h2 className="mt-6 text-2xl font-semibold leading-tight">
                  {selectedClip.title}
                </h2>

                <div className="mt-7 grid grid-cols-2 gap-3">
                  <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4">
                    <p className="text-xs text-zinc-500">Viral Score</p>
                    <p className="mt-1 text-xl font-semibold">
                      {selectedClip.score.toFixed(1)}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4">
                    <p className="text-xs text-zinc-500">Duration</p>
                    <p className="mt-1 text-xl font-semibold">
                      {selectedClip.duration}
                    </p>
                  </div>
                </div>
              </div>

              <button className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl bg-white py-3.5 text-sm font-semibold text-black transition hover:bg-zinc-200">
                <Download size={17} />
                Download Clip
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </main>
  );
}