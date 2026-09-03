"use client";

import {
  ArrowRight,
  Check,
  Clapperboard,
  Download,
  FileVideo,
  Link as LinkIcon,
  Loader2,
  Play,
  Scissors,
  Sparkles,
  Subtitles,
  Upload,
  X,
  Zap,
} from "lucide-react";

import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://galangclipper.com";

type JobStatus = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  step: string;
  message: string;
  clips_count?: number;
};

type Clip = {
  rank: number;
  video: string | null;
  score?: number;
  start?: number;
  end?: number;
  title?: string;
  text?: string;
  [key: string]: unknown;
};

const steps = [
  {
    key: "queued",
    label: "Queue",
    description: "Menunggu",
  },
  {
    key: "transcription",
    label: "AI Transcript",
    description: "Whisper",
  },
  {
    key: "viral_engine",
    label: "AI Analysis",
    description: "Viral moments",
  },
  {
    key: "clip_generation",
    label: "Top 5 Clips",
    description: "Generate",
  },
  {
    key: "vertical_renderer",
    label: "9:16 + Subtitle",
    description: "Social ready",
  },
];

function formatTime(seconds?: number) {
  if (
    seconds === undefined ||
    seconds === null ||
    Number.isNaN(Number(seconds))
  ) {
    return "--:--";
  }

  const total = Math.max(0, Math.floor(Number(seconds)));
  const minutes = Math.floor(total / 60);
  const secs = total % 60;

  return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function getVideoUrl(video: unknown) {
  if (typeof video !== "string" || !video.trim()) return "";
  const value = video.trim();
  if (value.startsWith("http://") || value.startsWith("https://")) return value;
  if (value.startsWith("/")) return `${API_URL}${value}`;
  return `${API_URL}/${value}`;
}

function getClipTitle(clip: Clip, index: number) {
  const candidates = [
    clip.title,
    clip.headline,
    clip.hook,
    clip.caption,
    clip.name,
    clip.topic,
  ];
  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  if (typeof clip.text === "string" && clip.text.trim()) {
    const clean = clip.text.replace(/\s+/g, " ").trim();
    const firstSentence = clean.split(/(?<=[.!?])\s+/)[0];
    return (firstSentence || clean).slice(0, 90);
  }
  return `Viral Moment ${index + 1}`;
}

function getStepIndex(step: string) {
  const index = steps.findIndex((item) => item.key === step);

  if (index !== -1) {
    return index;
  }

  if (step.includes("transcript")) return 1;
  if (step.includes("viral")) return 2;
  if (step.includes("clip")) return 3;
  if (step.includes("vertical")) return 4;
  if (step.includes("subtitle")) return 4;

  return 0;
}

export default function Home() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const [youtubeUrl, setYoutubeUrl] = useState("");

  const [inputMode, setInputMode] = useState<"file" | "url">("file");

  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);

  const [job, setJob] = useState<JobStatus | null>(null);

  const [clips, setClips] = useState<Clip[]>([]);

  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }

      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  // ============================================================
  // SELECT FILE
  // ============================================================

  const selectFile = (selectedFile: File | null) => {
    if (!selectedFile) return;

    if (!selectedFile.type.startsWith("video/")) {
      setError("File harus berupa video.");
      return;
    }

    const maxSize = 3 * 1024 * 1024 * 1024;

    if (selectedFile.size > maxSize) {
      setError("Ukuran video maksimal 3 GB.");
      return;
    }

    setError("");
    setFile(selectedFile);

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setPreview(URL.createObjectURL(selectedFile));

    setYoutubeUrl("");
    setJob(null);
    setClips([]);
    setShowResults(false);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    selectFile(event.target.files?.[0] || null);
  };

  // ============================================================
  // DROP
  // ============================================================

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);

    const droppedFile = event.dataTransfer.files?.[0];

    selectFile(droppedFile || null);
  };

  // ============================================================
  // REMOVE FILE
  // ============================================================

  const removeFile = () => {
    setFile(null);
    setJob(null);
    setClips([]);
    setShowResults(false);

    if (preview) {
      URL.revokeObjectURL(preview);
      setPreview(null);
    }

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  // ============================================================
  // RESET
  // ============================================================

  const resetAll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }

    setFile(null);
    setYoutubeUrl("");
    setJob(null);
    setClips([]);
    setError("");
    setGenerating(false);
    setUploading(false);
    setShowResults(false);

    if (preview) {
      URL.revokeObjectURL(preview);
      setPreview(null);
    }

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  // ============================================================
  // UPLOAD FILE
  // ============================================================

  const uploadVideo = async () => {
    if (!file) return false;

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();

      formData.append("file", file);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload video gagal.");
      }

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload video gagal.");

      return false;
    } finally {
      setUploading(false);
    }
  };

  // ============================================================
  // UPLOAD YOUTUBE URL
  // ============================================================

  const uploadYoutubeUrl = async () => {
    const url = youtubeUrl.trim();

    if (!url) {
      setError("Masukkan URL YouTube terlebih dahulu.");
      return false;
    }

    setUploading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/upload-url`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Gagal mengambil video YouTube.");
      }

      return true;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Gagal mengambil video YouTube.",
      );

      return false;
    } finally {
      setUploading(false);
    }
  };

  // ============================================================
  // LOAD CLIPS
  // ============================================================

  const loadClips = async () => {
    try {
      const response = await fetch(`${API_URL}/api/clips?t=${Date.now()}`, {
        cache: "no-store",
        headers: { "Cache-Control": "no-cache" },
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || "Gagal mengambil hasil clips.");

      const result: Clip[] = Array.isArray(data.clips)
        ? data.clips
            .map((clip: unknown, index: number) => {
              if (!clip || typeof clip !== "object") return null;
              const item = clip as Record<string, unknown>;
              return {
                ...item,
                rank: typeof item.rank === "number" ? item.rank : index + 1,
                video:
                  typeof item.video === "string"
                    ? item.video
                    : typeof item.video_url === "string"
                      ? item.video_url
                      : typeof item.url === "string"
                        ? item.url
                        : null,
              } as Clip;
            })
            .filter((clip: Clip | null): clip is Clip => clip !== null)
            .sort((a: Clip, b: Clip) => (a.rank ?? 999) - (b.rank ?? 999))
        : [];

      setClips(result);
      return result;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Gagal mengambil hasil clips.",
      );
      return [];
    }
  };

  const waitForAllClips = async (maxWaitMs = 45000) => {
    const startedAt = Date.now();
    let latest: Clip[] = [];

    while (Date.now() - startedAt < maxWaitMs) {
      latest = await loadClips();
      const withVideo = latest.filter((clip) =>
        Boolean(getVideoUrl(clip.video)),
      ).length;
      if (latest.length >= 5 && withVideo >= 5) return latest;
      if (latest.length >= 5 && withVideo === latest.length) return latest;
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    return latest;
  };

  // ============================================================
  // POLLING JOB
  // ============================================================

  const startPolling = (jobId: string) => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

    const checkJob = async () => {
      try {
        const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
          cache: "no-store",
        });

        const data = (await response.json()) as JobStatus;

        if (!response.ok) {
          throw new Error(
            (
              data as unknown as {
                detail?: string;
              }
            ).detail || "Gagal membaca status job.",
          );
        }

        setJob(data);

        // ================================================
        // COMPLETED
        // ================================================

        if (data.status === "completed") {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }

          setGenerating(false);

          // Tunggu renderer sampai Top 5 benar-benar tersedia.
          const result = await waitForAllClips(45000);

          if (result.length > 0) {
            setShowResults(true);

            const renderedCount = result.filter((clip) =>
              Boolean(getVideoUrl(clip.video)),
            ).length;

            if (result.length < 5 || renderedCount < 5) {
              setError(
                `Backend mengembalikan ${result.length} clip dan ${renderedCount} video siap. Target aplikasi adalah 5 video.`,
              );
            }

            setTimeout(() => {
              document.getElementById("results")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }, 300);
          } else {
            setError("Proses selesai tetapi clips belum ditemukan.");
          }

          return;
        }

        // ================================================
        // FAILED
        // ================================================

        if (data.status === "failed") {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }

          setGenerating(false);

          setError(data.message || "Proses pembuatan clip gagal.");
        }
      } catch (err) {
        if (pollRef.current) {
          clearInterval(pollRef.current);

          pollRef.current = null;
        }

        setGenerating(false);

        setError(
          err instanceof Error ? err.message : "Gagal membaca status proses.",
        );
      }
    };

    checkJob();

    pollRef.current = setInterval(checkJob, 2000);
  };

  // ============================================================
  // GENERATE
  // ============================================================

  const generateClips = async () => {
    if (inputMode === "file" && !file) {
      setError("Pilih video terlebih dahulu.");
      return;
    }

    if (inputMode === "url" && !youtubeUrl.trim()) {
      setError("Masukkan URL YouTube terlebih dahulu.");
      return;
    }

    setError("");
    setClips([]);
    setShowResults(false);
    setJob(null);

    let uploaded = false;

    if (inputMode === "url") {
      uploaded = await uploadYoutubeUrl();
    } else {
      uploaded = await uploadVideo();
    }

    if (!uploaded) {
      return;
    }

    setGenerating(true);

    try {
      const response = await fetch(`${API_URL}/api/generate`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Gagal memulai proses.");
      }

      setJob({
        id: data.job_id,
        status: "queued",
        step: "queued",
        message: "Menunggu proses...",
      });

      startPolling(data.job_id);
    } catch (err) {
      setGenerating(false);

      setError(err instanceof Error ? err.message : "Gagal memulai proses.");
    }
  };

  // ============================================================
  // PROGRESS
  // ============================================================

  const currentStep = job
    ? getStepIndex(job.step)
    : inputMode === "file" && file
      ? 0
      : inputMode === "url" && youtubeUrl
        ? 0
        : -1;

  const progress = job
    ? job.status === "completed"
      ? 100
      : job.status === "failed"
        ? 0
        : Math.min(
            95,
            Math.max(5, Math.round(((currentStep + 1) / steps.length) * 100)),
          )
    : file || youtubeUrl
      ? 10
      : 0;

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <main className="min-h-screen overflow-hidden bg-[#050507] text-white">
      {/* =====================================================
          BACKGROUND
      ====================================================== */}

      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-1/2 top-[-300px] h-[700px] w-[900px] -translate-x-1/2 rounded-full bg-violet-600/10 blur-[150px]" />

        <div className="absolute bottom-[-300px] left-[-200px] h-[600px] w-[600px] rounded-full bg-blue-600/10 blur-[150px]" />
      </div>

      {/* =====================================================
          NAVBAR
      ====================================================== */}

      <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#050507]/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 shadow-lg shadow-violet-500/20">
              <Scissors size={17} />
            </div>

            <div>
              <div className="text-sm font-bold tracking-tight">
                ClipForge
                <span className="text-violet-400">AI</span>
              </div>

              <div className="text-[8px] font-semibold tracking-[0.25em] text-white/35">
                PODCAST CLIPPER
              </div>
            </div>
          </div>

          <nav className="hidden items-center gap-8 text-xs text-white/50 md:flex">
            <a href="#features" className="transition hover:text-white">
              Features
            </a>

            <a href="#workflow" className="transition hover:text-white">
              How it works
            </a>

            <a href="#results" className="transition hover:text-white">
              Results
            </a>
          </nav>

          <button
            onClick={() =>
              document.getElementById("upload")?.scrollIntoView({
                behavior: "smooth",
              })
            }
            className="rounded-lg bg-white px-4 py-2 text-xs font-semibold text-black transition hover:bg-white/90"
          >
            Get Started
          </button>
        </div>
      </header>

      {/* =====================================================
          HERO
      ====================================================== */}

      <section className="relative mx-auto max-w-6xl px-5 pb-20 pt-20 lg:px-8 lg:pb-28 lg:pt-28">
        <div className="grid items-center gap-14 lg:grid-cols-[1fr_0.9fr]">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/[0.07] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-violet-300">
              <Sparkles size={11} />
              AI-Powered Podcast Clipping
            </div>

            <h1 className="max-w-2xl text-5xl font-black leading-[0.95] tracking-[-0.045em] sm:text-6xl lg:text-7xl">
              Turn long
              <br />
              podcasts into
              <br />
              <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-blue-400 bg-clip-text text-transparent">
                viral clips.
              </span>
            </h1>

            <p className="mt-7 max-w-xl text-sm leading-7 text-white/45 sm:text-base">
              ClipForge AI analyzes your podcast, discovers the strongest
              moments, creates the Top 5 clips and automatically converts them
              into social-ready 9:16 videos with subtitles.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={() =>
                  document.getElementById("upload")?.scrollIntoView({
                    behavior: "smooth",
                  })
                }
                className="group flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-black shadow-xl shadow-white/5 transition hover:-translate-y-0.5 hover:bg-white/90"
              >
                <Zap size={15} />
                Generate Viral Clips
                <ArrowRight
                  size={15}
                  className="transition group-hover:translate-x-1"
                />
              </button>

              <button
                onClick={() =>
                  document.getElementById("workflow")?.scrollIntoView({
                    behavior: "smooth",
                  })
                }
                className="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm font-medium text-white/70 transition hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
              >
                <Play size={14} />
                See how it works
              </button>
            </div>

            <div className="mt-7 flex flex-wrap gap-5 text-[10px] text-white/35">
              <span className="flex items-center gap-1.5">
                <Check size={12} className="text-emerald-400" />
                Local AI processing
              </span>

              <span className="flex items-center gap-1.5">
                <Check size={12} className="text-emerald-400" />
                Automatic subtitles
              </span>

              <span className="flex items-center gap-1.5">
                <Check size={12} className="text-emerald-400" />
                9:16 ready
              </span>
            </div>
          </div>

          {/* HERO MOCKUP */}

          <div className="relative">
            <div className="absolute -inset-10 rounded-full bg-violet-600/10 blur-3xl" />

            <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0c0a12] p-2 shadow-2xl shadow-violet-950/20">
              <div className="rounded-xl border border-white/10 bg-[#0a0810] p-5">
                <div className="mb-5 flex items-center justify-between">
                  <div className="flex gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-white/10" />
                    <span className="h-2 w-2 rounded-full bg-white/10" />
                    <span className="h-2 w-2 rounded-full bg-white/10" />
                  </div>

                  <span className="text-[8px] font-semibold tracking-[0.2em] text-white/20">
                    CLIPFORGE STUDIO
                  </span>
                </div>

                <div className="flex min-h-[290px] flex-col items-center justify-center rounded-xl border border-dashed border-violet-400/20 bg-violet-500/[0.025]">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/15 text-violet-300">
                    <Upload size={20} />
                  </div>

                  <p className="text-sm font-semibold">Upload your podcast</p>

                  <p className="mt-2 max-w-[220px] text-center text-[10px] leading-5 text-white/30">
                    Drag & drop your video here or browse from your computer.
                  </p>

                  <button
                    onClick={() =>
                      document.getElementById("upload")?.scrollIntoView({
                        behavior: "smooth",
                      })
                    }
                    className="mt-5 rounded-lg bg-white px-4 py-2 text-[10px] font-semibold text-black"
                  >
                    Choose video
                  </button>

                  <p className="mt-3 text-[8px] text-white/20">
                    MP4 · MOV · WEBM
                  </p>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-2">
                  {[
                    [Sparkles, "AI Analysis"],
                    [Scissors, "Top 5 Clips"],
                    [Subtitles, "Subtitles"],
                  ].map(([Icon, label], index) => {
                    const IconComponent = Icon as typeof Sparkles;

                    return (
                      <div
                        key={index}
                        className="rounded-lg border border-white/5 bg-white/[0.02] p-3"
                      >
                        <IconComponent size={12} className="text-violet-400" />

                        <p className="mt-2 text-[8px] text-white/40">
                          {label as string}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          STATS
      ====================================================== */}

      <section className="border-y border-white/[0.06] bg-white/[0.015]">
        <div className="mx-auto grid max-w-5xl grid-cols-2 divide-x divide-white/[0.06] md:grid-cols-4">
          {[
            ["01", "UPLOAD PODCAST"],
            ["05", "VIRAL MOMENTS"],
            ["9:16", "SOCIAL READY"],
            ["AI", "AUTO SUBTITLES"],
          ].map(([value, label]) => (
            <div
              key={label}
              className="flex flex-col items-center justify-center py-7"
            >
              <div className="text-lg font-bold">{value}</div>

              <div className="mt-1 text-[8px] font-semibold tracking-[0.18em] text-white/25">
                {label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* =====================================================
          UPLOAD
      ====================================================== */}

      <section
        id="upload"
        className="mx-auto max-w-4xl scroll-mt-24 px-5 py-24 lg:px-8"
      >
        <div className="mb-10 text-center">
          <div className="text-[9px] font-bold tracking-[0.25em] text-violet-400">
            START CREATING
          </div>

          <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
            Upload your podcast
          </h2>

          <p className="mt-3 text-sm text-white/35">
            Upload video atau masukkan URL YouTube.
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5 shadow-2xl shadow-black/20 sm:p-7">
          {/* MODE SWITCH */}

          <div className="mb-6 flex rounded-xl border border-white/10 bg-black/20 p-1">
            <button
              onClick={() => {
                setInputMode("file");
                setError("");
              }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-semibold transition ${
                inputMode === "file"
                  ? "bg-white text-black"
                  : "text-white/40 hover:text-white"
              }`}
            >
              <Upload size={14} />
              Upload Video
            </button>

            <button
              onClick={() => {
                setInputMode("url");
                setError("");
              }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-semibold transition ${
                inputMode === "url"
                  ? "bg-white text-black"
                  : "text-white/40 hover:text-white"
              }`}
            >
              <LinkIcon size={14} />
              YouTube URL
            </button>
          </div>

          {/* =================================================
              FILE MODE
          ================================================== */}

          {inputMode === "file" && (
            <>
              {!file ? (
                <div
                  onClick={() => inputRef.current?.click()}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}
                  className={`group flex min-h-[330px] cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed transition ${
                    dragging
                      ? "border-violet-400 bg-violet-500/10"
                      : "border-white/10 bg-black/20 hover:border-violet-400/30 hover:bg-violet-500/[0.03]"
                  }`}
                >
                  <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-400 transition group-hover:scale-105 group-hover:bg-violet-500/15">
                    <Upload size={25} />
                  </div>

                  <h3 className="text-lg font-bold">Upload your podcast</h3>

                  <p className="mt-2 text-center text-xs text-white/30">
                    Drag & drop video atau pilih dari PC.
                  </p>

                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();

                      inputRef.current?.click();
                    }}
                    className="mt-6 rounded-xl bg-white px-5 py-2.5 text-xs font-bold text-black"
                  >
                    Choose video
                  </button>

                  <p className="mt-3 text-[9px] text-white/20">
                    MP4 · MOV · MKV · WEBM · AVI
                  </p>
                </div>
              ) : (
                <div>
                  <div className="mb-5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400">
                        <FileVideo size={18} />
                      </div>

                      <div>
                        <p className="max-w-[260px] truncate text-xs font-semibold">
                          {file.name}
                        </p>

                        <p className="mt-1 text-[10px] text-white/30">
                          {(file.size / 1024 / 1024).toFixed(1)} MB
                        </p>
                      </div>
                    </div>

                    {!generating && (
                      <button
                        onClick={removeFile}
                        className="rounded-lg p-2 text-white/30 transition hover:bg-white/5 hover:text-white"
                      >
                        <X size={15} />
                      </button>
                    )}
                  </div>

                  {preview && (
                    <div className="overflow-hidden rounded-xl border border-white/10 bg-black">
                      <video
                        src={preview}
                        controls
                        className="max-h-[520px] w-full object-contain"
                      />
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* =================================================
              URL MODE
          ================================================== */}

          {inputMode === "url" && (
            <div className="rounded-xl border border-dashed border-violet-400/20 bg-violet-500/[0.025] p-6">
              <div className="mx-auto flex max-w-xl flex-col items-center text-center">
                <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 text-red-400">
                  <Play size={25} fill="currentColor" />
                </div>

                <h3 className="text-lg font-bold">Paste YouTube URL</h3>

                <p className="mt-2 text-xs text-white/30">
                  Masukkan link YouTube podcast yang ingin diproses.
                </p>

                <div className="mt-6 flex w-full flex-col gap-2 sm:flex-row">
                  <input
                    value={youtubeUrl}
                    onChange={(event) => setYoutubeUrl(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        generateClips();
                      }
                    }}
                    placeholder="https://www.youtube.com/watch?v=..."
                    disabled={uploading || generating}
                    className="h-11 flex-1 rounded-xl border border-white/10 bg-black/40 px-4 text-xs text-white outline-none placeholder:text-white/20 focus:border-violet-400/40"
                  />
                </div>

                <p className="mt-3 text-[9px] text-white/20">
                  YouTube · youtu.be · Shorts
                </p>
              </div>
            </div>
          )}

          {/* =================================================
              GENERATE BUTTON
          ================================================== */}

          {(file || youtubeUrl.trim()) && (
            <button
              onClick={generateClips}
              disabled={uploading || generating}
              className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-blue-500 py-3.5 text-xs font-bold shadow-lg shadow-violet-500/10 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading || generating ? (
                <>
                  <Loader2 size={15} className="animate-spin" />

                  {uploading
                    ? inputMode === "url"
                      ? "Mengambil video YouTube..."
                      : "Uploading..."
                    : "Generating Top 5 Clips..."}
                </>
              ) : (
                <>
                  <Sparkles size={15} />
                  Generate Top 5 Viral Clips
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          )}

          {/* =================================================
              PROCESS
          ================================================== */}

          {(job || generating) && (
            <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold">
                    {job?.message || "Memulai proses..."}
                  </p>

                  <p className="mt-1 text-[10px] text-white/30">
                    Jangan tutup halaman selama proses berlangsung.
                  </p>
                </div>

                <span className="text-xs font-bold text-violet-400">
                  {progress}%
                </span>
              </div>

              <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500 transition-all duration-700"
                  style={{
                    width: `${progress}%`,
                  }}
                />
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
                {steps.map((item, index) => {
                  const active = index <= currentStep;

                  const current =
                    index === currentStep &&
                    job?.status !== "completed" &&
                    job?.status !== "failed";

                  return (
                    <div key={item.key} className="flex items-center gap-2">
                      <div
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[9px] ${
                          active
                            ? "bg-violet-500/15 text-violet-300"
                            : "bg-white/5 text-white/20"
                        }`}
                      >
                        {active ? (
                          current ? (
                            <Loader2 size={12} className="animate-spin" />
                          ) : (
                            <Check size={12} />
                          )
                        ) : (
                          `0${index + 1}`
                        )}
                      </div>

                      <div className="min-w-0">
                        <p
                          className={`truncate text-[9px] font-semibold ${
                            active ? "text-white/80" : "text-white/25"
                          }`}
                        >
                          {item.label}
                        </p>

                        <p className="truncate text-[8px] text-white/20">
                          {item.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* =================================================
              ERROR
          ================================================== */}

          {error && (
            <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.06] p-4 text-xs text-red-300">
              <X size={15} className="mt-0.5 shrink-0" />

              <span>{error}</span>
            </div>
          )}
        </div>
      </section>

      {/* =====================================================
          FEATURES
      ====================================================== */}

      <section
        id="features"
        className="mx-auto max-w-6xl scroll-mt-24 px-5 py-24 lg:px-8"
      >
        <div className="max-w-2xl">
          <div className="text-[9px] font-bold tracking-[0.25em] text-violet-400">
            EVERYTHING AUTOMATED
          </div>

          <h2 className="mt-3 text-3xl font-black tracking-tight">
            From podcast to publish-ready.
          </h2>

          <p className="mt-4 text-sm leading-6 text-white/35">
            Tidak perlu mencari timestamp secara manual. ClipForge menangani
            proses dari transcript sampai video vertical.
          </p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            {
              icon: Sparkles,
              title: "AI Viral Detection",
              text: "Menganalisis hook, insight, emotion, story, curiosity dan faktor viral lainnya.",
            },
            {
              icon: Clapperboard,
              title: "Automatic 9:16",
              text: "Video landscape otomatis diubah menjadi format vertical untuk Reels, TikTok dan Shorts.",
            },
            {
              icon: Subtitles,
              title: "Burned-in Subtitles",
              text: "Subtitle dibuat berdasarkan transcript dan langsung dibakar ke video.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="group rounded-2xl border border-white/[0.08] bg-white/[0.025] p-6 transition hover:-translate-y-1 hover:border-violet-400/20 hover:bg-white/[0.04]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-300">
                <item.icon size={18} />
              </div>

              <h3 className="mt-5 text-sm font-bold">{item.title}</h3>

              <p className="mt-3 text-xs leading-6 text-white/35">
                {item.text}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* =====================================================
          WORKFLOW
      ====================================================== */}

      <section
        id="workflow"
        className="mx-auto max-w-5xl scroll-mt-24 px-5 py-24 lg:px-8"
      >
        <div className="text-center">
          <div className="text-[9px] font-bold tracking-[0.25em] text-violet-400">
            SIMPLE WORKFLOW
          </div>

          <h2 className="mt-3 text-3xl font-black">Three steps. That's it.</h2>
        </div>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {[
            ["01", "Upload", "Upload podcast video atau paste URL YouTube."],
            [
              "02",
              "AI Finds Moments",
              "Whisper membuat transcript lalu Viral Engine memilih 5 moment terbaik.",
            ],
            ["03", "Publish", "Download clip 9:16 lengkap dengan subtitle."],
          ].map(([number, title, text]) => (
            <div
              key={number}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.025] p-6"
            >
              <div className="text-xs font-bold text-violet-400">{number}</div>

              <h3 className="mt-8 text-sm font-bold">{title}</h3>

              <p className="mt-3 text-xs leading-6 text-white/35">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* =====================================================
          RESULTS
      ====================================================== */}

      <section
        id="results"
        className="mx-auto max-w-6xl scroll-mt-24 px-5 py-24 lg:px-8"
      >
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <div className="text-[9px] font-bold tracking-[0.25em] text-violet-400">
              YOUR OUTPUT
            </div>

            <h2 className="mt-3 text-3xl font-black">Your next viral clips</h2>

            <p className="mt-3 text-sm text-white/35">
              Video 9:16 dengan subtitle sudah siap dipublish.
            </p>
          </div>

          {clips.length > 0 && (
            <div className="rounded-full border border-emerald-400/20 bg-emerald-400/5 px-3 py-1.5 text-[10px] font-semibold text-emerald-300">
              {clips.length} clips ready
            </div>
          )}
        </div>

        {showResults && clips.length > 0 ? (
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {clips.map((clip, index) => {
              const videoUrl = getVideoUrl(clip.video);

              return (
                <div
                  key={clip.rank ?? index}
                  className="group overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.025] transition hover:-translate-y-1 hover:border-violet-400/20"
                >
                  <div className="relative aspect-[9/16] overflow-hidden bg-black">
                    {videoUrl ? (
                      <video
                        src={videoUrl}
                        controls
                        preload="metadata"
                        playsInline
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-xs text-white/30">
                        <Loader2
                          size={22}
                          className="animate-spin text-violet-400"
                        />
                        <span>Video sedang dirender...</span>
                      </div>
                    )}

                    <div className="pointer-events-none absolute left-3 top-3 rounded-lg bg-black/70 px-2.5 py-1.5 text-[10px] font-bold backdrop-blur">
                      #{String(clip.rank ?? index + 1).padStart(2, "0")}
                    </div>
                  </div>

                  <div className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-violet-300">
                          Clip #
                          {String(clip.rank ?? index + 1).padStart(2, "0")}
                        </p>

                        <h3 className="mt-1 line-clamp-2 text-sm font-bold leading-5 text-white">
                          {getClipTitle(clip, index)}
                        </h3>

                        <p className="mt-1 text-[10px] text-white/30">
                          {formatTime(clip.start)} → {formatTime(clip.end)}
                        </p>
                      </div>

                      {typeof clip.score === "number" && (
                        <div className="rounded-lg bg-violet-500/10 px-2 py-1 text-[10px] font-bold text-violet-300">
                          {clip.score.toFixed(1)}
                        </div>
                      )}
                    </div>

                    {clip.text && (
                      <p className="mt-3 line-clamp-3 text-[10px] leading-5 text-white/35">
                        {clip.text}
                      </p>
                    )}

                    {videoUrl && (
                      <a
                        href={videoUrl}
                        download
                        target="_blank"
                        rel="noreferrer"
                        className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] py-2.5 text-[10px] font-semibold transition hover:bg-white/[0.07]"
                      >
                        <Download size={13} />
                        Download Clip
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="mt-10 flex min-h-[260px] flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.015] text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400">
              {generating ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Clapperboard size={20} />
              )}
            </div>

            <h3 className="mt-5 text-sm font-semibold">
              {generating ? "Creating your viral clips..." : "No clips yet"}
            </h3>

            <p className="mt-2 max-w-sm text-xs leading-5 text-white/30">
              {generating
                ? job?.message || "AI sedang memproses podcast kamu."
                : "Upload podcast lalu generate Top 5 untuk melihat hasil di sini."}
            </p>
          </div>
        )}
      </section>

      {/* =====================================================
          FOOTER
      ====================================================== */}

      <footer className="border-t border-white/[0.06]">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-8 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left lg:px-8">
          <div className="flex items-center justify-center gap-2 sm:justify-start">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-500/15 text-violet-300">
              <Scissors size={12} />
            </div>

            <span className="text-xs font-bold">
              ClipForge
              <span className="text-violet-400">AI</span>
            </span>
          </div>

          <p className="text-[10px] text-white/20">
            AI-powered podcast clipping · Version 5.3
          </p>
        </div>
      </footer>

      {/* =====================================================
          HIDDEN FILE INPUT
      ====================================================== */}

      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/quicktime,video/x-matroska,video/webm,video/x-msvideo"
        onChange={handleFileChange}
        className="hidden"
      />
    </main>
  );
}
