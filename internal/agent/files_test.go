package agent

import (
	"context"
	"fmt"
	"reflect"
	"testing"
	"time"

	"golang.org/x/sync/errgroup"
)

type uploadFileFunc func(ctx context.Context, path string) (string, error)

func uploadFilesSequential(ctx context.Context, filePaths []string, uploadFn uploadFileFunc) ([]string, error) {
	var uris []string
	for _, path := range filePaths {
		uri, err := uploadFn(ctx, path)
		if err != nil {
			return nil, fmt.Errorf("failed to upload %s: %w", path, err)
		}
		if uri != "" {
			uris = append(uris, uri)
		}
	}
	return uris, nil
}

func uploadFilesConcurrent(ctx context.Context, filePaths []string, uploadFn uploadFileFunc) ([]string, error) {
	if len(filePaths) == 0 {
		return nil, nil
	}

	g, ctx := errgroup.WithContext(ctx)
	uris := make([]string, len(filePaths))

	for i, path := range filePaths {
		g.Go(func() error {
			uri, err := uploadFn(ctx, path)
			if err != nil {
				return fmt.Errorf("failed to upload %s: %w", path, err)
			}
			uris[i] = uri
			return nil
		})
	}

	if err := g.Wait(); err != nil {
		return nil, err
	}

	result := make([]string, 0, len(uris))
	for _, uri := range uris {
		if uri != "" {
			result = append(result, uri)
		}
	}
	return result, nil
}

func TestUploadFilesConcurrentPreservesOrder(t *testing.T) {
	paths := []string{"a.txt", "b.txt", "c.txt", "d.txt"}
	mockUpload := func(ctx context.Context, path string) (string, error) {
		if path == "a.txt" {
			time.Sleep(30 * time.Millisecond)
		} else {
			time.Sleep(5 * time.Millisecond)
		}
		return "uri://" + path, nil
	}

	uris, err := uploadFilesConcurrent(t.Context(), paths, mockUpload)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	want := []string{"uri://a.txt", "uri://b.txt", "uri://c.txt", "uri://d.txt"}
	if !reflect.DeepEqual(uris, want) {
		t.Fatalf("got uris %v, want %v", uris, want)
	}
}

func TestUploadFilesConcurrentErrorHandling(t *testing.T) {
	paths := []string{"a.txt", "fail.txt", "c.txt"}
	mockUpload := func(ctx context.Context, path string) (string, error) {
		if path == "fail.txt" {
			return "", fmt.Errorf("upload error")
		}
		return "uri://" + path, nil
	}

	_, err := uploadFilesConcurrent(t.Context(), paths, mockUpload)
	if err == nil {
		t.Fatal("expected error, got nil")
	}
}

func BenchmarkUploadFiles_Sequential(b *testing.B) {
	paths := []string{"file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"}
	mockUpload := func(ctx context.Context, path string) (string, error) {
		time.Sleep(10 * time.Millisecond)
		return "uri://" + path, nil
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := uploadFilesSequential(context.Background(), paths, mockUpload)
		if err != nil {
			b.Fatal(err)
		}
	}
}

func BenchmarkUploadFiles_Concurrent(b *testing.B) {
	paths := []string{"file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"}
	mockUpload := func(ctx context.Context, path string) (string, error) {
		time.Sleep(10 * time.Millisecond)
		return "uri://" + path, nil
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := uploadFilesConcurrent(context.Background(), paths, mockUpload)
		if err != nil {
			b.Fatal(err)
		}
	}
}
