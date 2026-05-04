package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/twmb/franz-go/pkg/kgo"
)

type userResp struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

var kclient *kgo.Client

func batchHandler(w http.ResponseWriter, r *http.Request) {
	tail := strings.TrimPrefix(r.URL.Path, "/users/batch/")
	n, err := strconv.Atoi(tail)
	if err != nil || n < 1 {
		http.Error(w, "bad n", http.StatusBadRequest)
		return
	}

	ctx := r.Context()
	for i := 1; i <= n; i++ {
		u := userResp{
			ID:    uuid.NewString(),
			Name:  "user_" + strconv.Itoa(i),
			Email: "user_" + strconv.Itoa(i) + "@example.com",
		}
		value, _ := json.Marshal(&u)
		kclient.Produce(ctx, &kgo.Record{
			Topic: "users",
			Key:   []byte(u.ID),
			Value: value,
		}, nil)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]int{"sent": n})
}

func main() {
	broker := os.Getenv("KAFKA_BOOTSTRAP_SERVERS")
	if broker == "" {
		broker = "kafka:9092"
	}

	var err error
	kclient, err = kgo.NewClient(
		kgo.SeedBrokers(broker),
		kgo.ProducerLinger(20*time.Millisecond),
		kgo.ProducerBatchMaxBytes(65536),
		kgo.ProducerBatchCompression(kgo.Lz4Compression()),
		kgo.RequiredAcks(kgo.LeaderAck()),
		kgo.DisableIdempotentWrite(),
	)
	if err != nil {
		log.Fatal(err)
	}
	defer kclient.Close()

	if err := kclient.Ping(context.Background()); err != nil {
		log.Printf("kafka ping failed: %v", err)
	}

	http.HandleFunc("/users/batch/", batchHandler)
	log.Println("Listening on :8001")
	log.Fatal(http.ListenAndServe(":8001", nil))
}
