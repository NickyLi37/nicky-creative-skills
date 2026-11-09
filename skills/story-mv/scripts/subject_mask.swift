// Cut the foreground subjects out of a still with macOS Vision (the same subject lifting as Photos).
// Build once: swiftc -O subject_mask.swift -o subject_mask   (macOS 14 or later)
// usage: ./subject_mask IN.png OUT_PREFIX  ->  OUT_PREFIX_all.f32 and OUT_PREFIX_<i>.f32
// Each file is a raw float32 mask (0..1) at the image size, row by row; title_cover.py reads it directly.
// Check the mask at full size before using it: stray parts (a tail tip above a head) and edge fringes show there.
import Foundation
import Vision
import CoreVideo

let args = CommandLine.arguments
guard args.count >= 3 else { print("usage: subject_mask IN.png OUT_PREFIX"); exit(2) }
let handler = VNImageRequestHandler(url: URL(fileURLWithPath: args[1]), options: [:])
let req = VNGenerateForegroundInstanceMaskRequest()
do { try handler.perform([req]) } catch { print("perform failed: \(error)"); exit(1) }
guard let obs = req.results?.first else { print("no subject found"); exit(1) }
let all = obs.allInstances
print("instances:", Array(all))

func saveRaw(_ pb: CVPixelBuffer, _ path: String) {
    CVPixelBufferLockBaseAddress(pb, .readOnly)
    let w = CVPixelBufferGetWidth(pb), h = CVPixelBufferGetHeight(pb)
    let bpr = CVPixelBufferGetBytesPerRow(pb)
    let base = CVPixelBufferGetBaseAddress(pb)!
    var data = Data(capacity: w * h * 4)
    for y in 0..<h {
        data.append(base.advanced(by: y * bpr).assumingMemoryBound(to: UInt8.self), count: w * 4)
    }
    CVPixelBufferUnlockBaseAddress(pb, .readOnly)
    try! data.write(to: URL(fileURLWithPath: path))
    print("wrote", path, w, h, CVPixelBufferGetPixelFormatType(pb))
}
do {
    saveRaw(try obs.generateScaledMaskForImage(forInstances: all, from: handler), args[2] + "_all.f32")
    for i in all {
        saveRaw(try obs.generateScaledMaskForImage(forInstances: IndexSet(integer: i), from: handler), args[2] + "_\(i).f32")
    }
} catch { print("mask failed: \(error)"); exit(1) }
