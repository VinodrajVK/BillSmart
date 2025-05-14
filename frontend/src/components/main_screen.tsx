import React, { useState, useRef, useEffect } from "react";
import Webcam from "react-webcam";
import { Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, Typography, AppBar, Toolbar, Container, Card, CardContent, Box, Link } from "@mui/material";

const CameraItemList: React.FC = () => {
  const webcamRef = useRef<Webcam>(null);
  const [image, setImage] = useState<string | null>(null);
  const [items, setItems] = useState<{ name: string; count: number; price: number }[]>([]);
  const [totalAmount, setTotalAmount] = useState<number>(0);
  const [billId, setBillId] = useState<string | null>(null);
  const [deviceId, setDeviceId] = useState<string | null>(null);

  useEffect(() => {
    navigator.mediaDevices.enumerateDevices().then((devices) => {
      const videoDevices = devices.filter((device) => device.kind === "videoinput");

      // Find DroidCam (or any external webcam)
      const externalCam = videoDevices.find((device) => device.label.toLowerCase().includes("droidcam"));
      
      if (externalCam) {
        setDeviceId(externalCam.deviceId);
      } else if (videoDevices.length > 1) {
        setDeviceId(videoDevices[1].deviceId); // Fallback to second webcam
      } else {
        setDeviceId(videoDevices[0]?.deviceId || null); // Use default
      }
    });
  }, []);

  const captureImage = () => {
    if (webcamRef.current) {
      const capturedImage = webcamRef.current.getScreenshot();
      setImage(capturedImage);
    }
  };

  const retakeImage = () => {
    setImage(null);
    setItems([]);
    setTotalAmount(0);
    setBillId(null);
  };

  const submitImage = async () => {
    if (!image) return;

    const blob = await fetch(image).then((res) => res.blob());
    const file = new File([blob], "captured.jpg", { type: "image/jpeg" });
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/process_image/", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      if (response.ok) {
        setItems(result.items || []);
        calculateTotal(result.items);
      } else {
        console.error("Error:", result.error);
      }
    } catch (error) {
      console.error("Error sending image to backend:", error);
    }
  };

  const calculateTotal = (items: { name: string; count: number; price: number }[]) => {
    const total = items.reduce((acc, item) => acc + item.count * item.price, 0);
    setTotalAmount(total);
    speakTotalAmount(total);
  };

  const handleEdit = (index: number, key: "count" | "price", value: number) => {
    const updatedItems = [...items];
    updatedItems[index][key] = value;
    setItems(updatedItems);
    calculateTotal(updatedItems);
  };

  const generateBill = async () => {
    try {
      const response = await fetch("http://localhost:8000/generate_bill/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(items),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      // Handle PDF response and download it
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "bill.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error generating bill:", error);
    }
  };

  const speakTotalAmount = (amount: number) => {
    const speech = new SpeechSynthesisUtterance(`Total amount is ${amount} rupees`);
    speechSynthesis.speak(speech);
  };

  return (
    <Container maxWidth="lg">
      <AppBar position="static" sx={{ bgcolor: "#1565C0", mb: 3 }}>
        <Toolbar>
          <Typography variant="h5" sx={{ flexGrow: 1, fontWeight: "bold" }}>
            BillSmart
          </Typography>
        </Toolbar>
      </AppBar>

      <Box display="flex" gap={4}>
        <Card sx={{ flex: 1, p: 2, borderRadius: 2, boxShadow: 3 }}>
          <CardContent sx={{ textAlign: "center" }}>
            {!image ? (
              <>
                {deviceId ? (
                  <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    videoConstraints={{ deviceId }}
                    style={{ width: "100%", borderRadius: "10px" }}
                  />
                ) : (
                  <Typography color="error">No external webcam detected</Typography>
                )}
                <Button variant="contained" sx={{ mt: 2, bgcolor: "#1565C0" }} onClick={captureImage}>
                  Capture Image
                </Button>
              </>
            ) : (
              <>
                <img src={image} alt="Captured" style={{ width: "100%", borderRadius: "10px" }} />
                <Box mt={2}>
                  <Button variant="contained" sx={{ bgcolor: "#E53935", mr: 2 }} onClick={retakeImage}>
                    Retake Image
                  </Button>
                  <Button variant="contained" sx={{ bgcolor: "#1565C0" }} onClick={submitImage}>
                    Submit Image
                  </Button>
                </Box>
              </>
            )}
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, p: 2, borderRadius: 2, boxShadow: 3 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Item List
            </Typography>
            <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: "#1565C0" }}>
                    <TableCell sx={{ color: "white", fontWeight: "bold" }}>Item Name</TableCell>
                    <TableCell sx={{ color: "white", fontWeight: "bold" }}>Count</TableCell>
                    <TableCell sx={{ color: "white", fontWeight: "bold" }}>Price (₹)</TableCell>
                    <TableCell sx={{ color: "white", fontWeight: "bold" }}>Total (₹)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {items.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>
                        <TextField type="number" value={item.count} onChange={(e) => handleEdit(index, "count", Number(e.target.value))} size="small" sx={{ width: "60px" }} />
                      </TableCell>
                      <TableCell>
                        <TextField type="number" value={item.price} onChange={(e) => handleEdit(index, "price", Number(e.target.value))} size="small" sx={{ width: "80px" }} />
                      </TableCell>
                      <TableCell>₹{item.count * item.price}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
                      </TableContainer>
                      <Typography variant="h6" sx={{ mt: 3, fontWeight: "bold" }}>Total Amount: ₹{totalAmount}</Typography>
            <Button variant="contained" sx={{ mt: 2, bgcolor: "#2E7D32" }} onClick={generateBill}>
              Generate Bill
            </Button>
            {billId && (
              <Box mt={2}>
                <Link href={`http://localhost:8000/download_bill/${billId}`} target="_blank" rel="noopener noreferrer">Download Bill</Link>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default CameraItemList;
