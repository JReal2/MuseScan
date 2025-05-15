"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { ArrowLeft, Download, FileImage, Loader2, MusicIcon, Play, Square } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FileUploader } from "@/components/file-uploader"
import { MidiPlayer } from "@/components/midi-player"
import { convertSheetToMidi } from "@/lib/sheet-to-midi"

export default function ConverterPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [midiUrl, setMidiUrl] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [activeTab, setActiveTab] = useState("upload")

  const handleFileChange = (file: File | null) => {
    if (!file) return

    setFile(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      setPreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)
    setActiveTab("preview")
  }

  const handleConvert = async () => {
    if (!file) return

    setIsProcessing(true)
    setProgress(0)

    // Simulate progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval)
          return 95
        }
        return prev + 5
      })
    }, 200)

    try {
      // This is a simulated conversion - in a real app, this would call an API
      const result = await convertSheetToMidi(file)
      setMidiUrl(result.midiUrl)
      setProgress(100)
      setActiveTab("result")
    } catch (error) {
      console.error("Conversion failed:", error)
    } finally {
      clearInterval(interval)
      setIsProcessing(false)
    }
  }

  const handlePlay = () => {
    setIsPlaying(!isPlaying)
  }

  const handleDownload = () => {
    if (!midiUrl) return

    const link = document.createElement("a")
    link.href = midiUrl
    link.download = `${file?.name.split(".")[0] || "sheet-music"}.mid`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <MusicIcon className="h-5 w-5" />
            <span>MuseScan</span>
          </Link>
        </div>
      </header>
      <main className="flex-1 py-8">
        <div className="container">
          <div className="mb-8 flex items-center">
            <Button variant="ghost" size="sm" asChild className="gap-1">
              <Link href="/">
                <ArrowLeft className="h-4 w-4" />
                Back to Home
              </Link>
            </Button>
            <Separator orientation="vertical" className="mx-4 h-6" />
            <h1 className="text-2xl font-bold">Sheet Music Converter</h1>
          </div>

          <div className="mx-auto max-w-3xl">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="upload">Upload</TabsTrigger>
                <TabsTrigger value="preview" disabled={!file}>
                  Preview
                </TabsTrigger>
                <TabsTrigger value="result" disabled={!midiUrl}>
                  Result
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="mt-6">
                <Card>
                  <CardContent className="pt-6">
                    <FileUploader onFileChange={handleFileChange} />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="preview" className="mt-6">
                <Card>
                  <CardContent className="pt-6">
                    {preview && (
                      <div className="space-y-4">
                        <div className="overflow-hidden rounded-lg border">
                          <Image
                            src={preview || "/placeholder.svg"}
                            alt="Sheet music preview"
                            width={800}
                            height={600}
                            className="mx-auto max-h-[400px] w-auto object-contain"
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <FileImage className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">{file?.name}</span>
                          </div>
                          <Button onClick={handleConvert} disabled={isProcessing}>
                            {isProcessing ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Converting...
                              </>
                            ) : (
                              "Convert to MIDI"
                            )}
                          </Button>
                        </div>
                        {isProcessing && (
                          <div className="space-y-2">
                            <Progress value={progress} className="h-2 w-full" />
                            <p className="text-xs text-center text-muted-foreground">
                              {progress < 100 ? "Analyzing sheet music and generating MIDI..." : "Conversion complete!"}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="result" className="mt-6">
                <Card>
                  <CardContent className="pt-6">
                    {midiUrl && (
                      <div className="space-y-6">
                        <div className="flex flex-col items-center justify-center space-y-4 rounded-lg border bg-muted/40 p-6">
                          <div className="text-center">
                            <h3 className="text-lg font-medium">Your MIDI file is ready!</h3>
                            <p className="text-sm text-muted-foreground">
                              You can play it below or download it to your computer.
                            </p>
                          </div>

                          <MidiPlayer midiUrl={midiUrl} isPlaying={isPlaying} onTogglePlay={handlePlay} />

                          <div className="flex gap-4">
                            <Button
                              variant={isPlaying ? "destructive" : "default"}
                              onClick={handlePlay}
                              className="gap-2"
                            >
                              {isPlaying ? (
                                <>
                                  <Square className="h-4 w-4" />
                                  Stop
                                </>
                              ) : (
                                <>
                                  <Play className="h-4 w-4" />
                                  Play
                                </>
                              )}
                            </Button>
                            <Button variant="outline" onClick={handleDownload} className="gap-2">
                              <Download className="h-4 w-4" />
                              Download MIDI
                            </Button>
                          </div>
                        </div>

                        <div className="rounded-lg border p-4">
                          <h3 className="mb-2 font-medium">Original Sheet Music</h3>
                          {preview && (
                            <Image
                              src={preview || "/placeholder.svg"}
                              alt="Original sheet music"
                              width={800}
                              height={300}
                              className="mx-auto max-h-[200px] w-auto object-contain"
                            />
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </main>
    </div>
  )
}
