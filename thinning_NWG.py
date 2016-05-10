#encoding: utf-8
#
# 細線化(Nagendraprasad-Wang-Gupta)
#

import cv2
import numpy as np

def ProcNWG():
  Point[] p = {new Point(0, -1),
               new Point(1, -1),
               new Point(1, 0),
               new Point(1, 1),
               new Point(0, 1),
               new Point(-1, 1),
               new Point(-1, 0),
               new Point(-1, -1)};
    
  List<Point> lst = new List<Point>();
  int a, s, c;
  int[] t = new int[8];
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
          for (int i = 0; i < 8; i++)
          {
            t[i] = b[x + p[i].X, y + p[i].Y];
          }
          // 外周の並び調査
          a = 0; f = false;
          for (int i = 0; i < 8; i++)
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
          if (t[0] + t[7] == 2 && a > 1) a--;
          // 外周の合計取得
          s = 0;
          for (int i = 0; i < 8; i++) s += t[i];
          // 合計が2以上6以下の場合
          if (s >= 2 && s <= 6)
          {
            c = 0;
            if (((t[0] + t[1] + t[2] + t[5] == 0) && (t[4] + t[6] == 2)) ||
                ((t[2] + t[3] + t[4] + t[7] == 0) && (t[0] + t[6] == 2)))
            {
              c = 1;
            }
            if (a == 1 || c == 1)
            {
              if ((t[2] + t[4]) * t[0] * t[6] == 0)
              {
                // 削除リストに加える（此処で削除しては駄目？）
                lst.Add(new Point(x, y));
              }
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
          if (b[x, y] == 1)
          {
            // 8近傍の情報取得
            for (int i = 0; i < 8; i++)
            {
              t[i] = b[x + p[i].X, y + p[i].Y];
            }
            // 外周の並び調査
            a = 0; f = false;
            for (int i = 0; i < 8; i++)
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
            if (t[0] + t[7] == 2 && a > 1) a--;
            // 外周の合計取得
            s = 0;
            for (int i = 0; i < 8; i++) s += t[i];
            // 合計が2以上6以下の場合
            if (s >= 2 && s <= 6)
            {
              c = 0;
              if (((t[0] + t[1] + t[2] + t[5] == 0) && (t[4] + t[6] == 2)) ||
                  ((t[2] + t[3] + t[4] + t[7] == 0) && (t[0] + t[6] == 2)))
              {
                c = 1;
              }
              if (a == 1 || c == 1)
              {
                if ((t[0] + t[6]) * t[2] * t[4] == 0)
                {
                  // 削除リストに加える（此処で削除しては駄目？）
                  lst.Add(new Point(x, y));
                }
              }
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