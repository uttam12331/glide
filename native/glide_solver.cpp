// glide_solver.cpp
//
// A fast C++17 re-implementation of GLIDE's slide-to-fill solver, exposed to
// Python through a tiny C ABI (loaded with ctypes -- see glide/native_solver.py).
//
// The Python solver in glide/solver.py uses Python sets of frozensets; this
// version packs each board state into two integers -- the orb's cell index and
// a 64-bit bitmask of lit tiles -- so a whole state is a single uint64 key in a
// hash set. That is dramatically faster and is the kind of hot-path-in-C++,
// glue-in-Python split that game engines (Panda3D included) are built on.
//
// Build: see native/CMakeLists.txt. No engine headers required.

#include <cstdint>
#include <queue>
#include <unordered_set>
#include <vector>

#if defined(_WIN32)
#define GLIDE_API extern "C" __declspec(dllexport)
#else
#define GLIDE_API extern "C"
#endif

namespace {

// Board limited to 64 cells so the "filled" set fits in a single uint64 mask.
constexpr int kMaxCells = 64;

struct Board {
    int w = 0, h = 0;
    int start = -1;
    uint64_t walls = 0;   // 1 bit per wall/gap cell
    uint64_t stops = 0;   // 1 bit per stop tile
    uint64_t target = 0;  // 1 bit per fillable cell (the win condition)
};

inline bool parse(const char* grid, int w, int h, Board& b) {
    if (w <= 0 || h <= 0 || w * h > kMaxCells) return false;
    b.w = w;
    b.h = h;
    for (int i = 0; i < w * h; ++i) {
        char c = grid[i];
        const uint64_t bit = uint64_t(1) << i;
        if (c == '#' || c == ' ') {
            b.walls |= bit;
        } else {                      // '.', 'o', or 's' -> a fillable cell
            b.target |= bit;
            if (c == 'o') b.start = i;
            if (c == 's') b.stops |= bit;
        }
    }
    return b.start >= 0;
}

// One slide. Returns the resulting cell index and updates `mask`, or -1 if the
// move makes no progress. Mirrors slide() in glide/level.py exactly.
inline int slide(const Board& b, int player, uint64_t& mask, int dr, int dc) {
    int r = player / b.w, c = player % b.w;
    int cur = player;
    bool moved = false;
    while (true) {
        int nr = r + dr, nc = c + dc;
        if (nr < 0 || nr >= b.h || nc < 0 || nc >= b.w) break;
        int ni = nr * b.w + nc;
        const uint64_t bit = uint64_t(1) << ni;
        if (b.walls & bit) break;      // wall / edge
        if (mask & bit) break;         // our own lit trail
        r = nr;
        c = nc;
        cur = ni;
        mask |= bit;
        moved = true;
        if (b.stops & bit) break;      // stop tile halts the slide
    }
    return moved ? cur : -1;
}

inline uint64_t key(int player, uint64_t mask) {
    // player < 64 fits in 6 bits; shifting by 40 leaves room for a 36+ bit mask.
    return (uint64_t(player) << 40) ^ mask;
}

}  // namespace

// Returns the minimum number of moves to light every tile, or -1 if unsolvable
// (or the board is invalid / too large).
GLIDE_API int glide_solve_par(const char* grid, int w, int h) {
    Board b;
    if (!parse(grid, w, h, b)) return -1;

    uint64_t start_mask = uint64_t(1) << b.start;
    if ((start_mask & b.target) == b.target) return 0;

    const int dirs[4][2] = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
    std::unordered_set<uint64_t> seen;
    seen.reserve(1 << 16);
    seen.insert(key(b.start, start_mask));

    std::queue<std::pair<int, uint64_t>> frontier;  // (player, mask)
    std::queue<int> depths;
    frontier.push({b.start, start_mask});
    depths.push(0);

    while (!frontier.empty()) {
        auto [player, mask] = frontier.front();
        frontier.pop();
        int depth = depths.front();
        depths.pop();

        for (auto& d : dirs) {
            uint64_t nmask = mask;
            int np = slide(b, player, nmask, d[0], d[1]);
            if (np < 0) continue;
            if ((nmask & b.target) == b.target) return depth + 1;
            uint64_t k = key(np, nmask);
            if (seen.insert(k).second) {
                frontier.push({np, nmask});
                depths.push(depth + 1);
            }
        }
    }
    return -1;
}

// Simple version probe so the Python side can confirm it loaded the library.
GLIDE_API int glide_abi_version() { return 1; }
