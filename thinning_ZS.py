#
#
# 細線化(Zhang-Suen)
#

private void ProcZhangSuen()
{
  Point[] p = {new Point(0, 0),
               new Point(0, -1),
               new Point(1, -1),
               new Point(1, 0),
               new Point(1, 1),
               new Point(0, 1),
               new Point(-1, 1),
               new Point(-1, 0),
               new Point(-1, -1)};
    
  List<Point> lst = new List<Point>();
  int a, s;
  int[] t = new int[9];
  bool f;
    
  // 元画像をInteger配列に取込
  int[,] b = new int[bs.Width, bs.Height];
  for (int y = 0; y < bs.Height; y++)
  {
    for (int x = 0; x < bs.Width; x++)
    {
      if (bs.GetPixel(x, y).GetBrightness() >= 0.5f) b[x, y] = 1;
      else b[x, y] = 0;
    }
  }
  
  do
  {
    // パターン1
    lst.Clear();
    for (int y = 1; y < bs.Height - 1; y++)
    {
      for (int x = 1; x < bs.Width - 1; x++)
      {
        if (b[x, y] == 1)
        {
          // 8近傍の情報取得
          for (int i = 0; i < 9; i++)
          {
            t[i] = b[x + p[i].X, y + p[i].Y];
          }
          // 外周の並び調査
          a = 0; f = false;
          for (int i = 1; i<9; i++)
          {
            if (t[i] == 1)
            {
              if (!f)
              {
                a++; f = true;
              }
            }
            else
            {
              f = false;
            }
          }
          if (t[1] + t[8] == 2 && a > 1) a--;
          // 外周の合計取得
          s = 0;
          for (int i = 1; i < 9; i++) s += t[i];
          // 外周で白の並びが1個で、合計が2以上6以下の場合
          if (a == 1 && (s >= 2 && s <= 6))
          {
            if (t[1] * t[3] * t[5] == 0 && t[3] * t[5] * t[7] == 0)
            {
              // 削除リストに加える（此処で削除しては駄目）
              lst.Add(new Point(x, y));
            }
          }
        }
      }
    }
    // パターン2
    if (lst.Count > 0)
    {
      // 削除リストに登録された画素を削除
      for (int i = 0; i < lst.Count; i++)
      {
        b[lst[i].X, lst[i].Y] = 0;
      }
      lst.Clear();
      for (int y = 1; y < bs.Height - 1; y++)
      {
        for (int x = 1; x < bs.Width - 1; x++)
        {
          // 8近傍の情報取得
          for (int i = 0; i < 9; i++)
          {
            t[i] = b[x + p[i].X, y + p[i].Y];
          }
          // 外周の並び調査
          a = 0; f = false;
          for (int i = 1; i < 9; i++)
          {
            if (t[i] == 1)
            {
              if (!f)
              {
                a++; f = true;
              }
            }
            else
            {
              f = false;
            }
          }
          if (t[1] + t[8] == 2 && a > 1) a--;
          // 外周の合計取得
          s = 0;
          for (int i = 1; i < 9; i++) s += t[i];
          // 外周で白の並びが1個で、合計が2以上6以下の場合
          if (a == 1 && (s >= 2 && s <= 6))
          {
            if (t[1] * t[3] * t[7] == 0 && t[1] * t[5] * t[7] == 0)
            {
              // 削除リストに加える（此処で削除しては駄目）
              lst.Add(new Point(x, y));
            }
          }
        }
      }
      // 削除リストに登録された画素を削除
      for (int i = 0; i < lst.Count; i++)
      {
        b[lst[i].X, lst[i].Y] = 0;
      }
    }
  } while (lst.Count > 0);
  
  // 描画
  for (int y = 0; y < bs.Height; y++)
  {
    for (int x = 0; x < bs.Width; x++)
    {
      if (b[x, y] == 0)
        bd.SetPixel(x, y, Color.FromArgb(255, 0, 0, 0));
      else
        bd.SetPixel(x, y, Color.FromArgb(255, 255, 255, 255));
    }
  }
  picDest.Refresh();
}
